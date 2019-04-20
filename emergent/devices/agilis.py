import sys
import os
import numpy as np
from emergent.protocols import serial
import serial as ser
from emergent.core import Device
from emergent.core import ProcessHandler
import time

def getChar():
    ''' Returns a user-input keyboard character. Cross-platform implementation
        credited to Matthew Strax-Haber (StackExchange) '''
    # figure out which function to use once, and store it in _func
    if "_func" not in getChar.__dict__:
        try:
            # for Windows-based systems
            import msvcrt # If successful, we are on Windows
            getChar._func=msvcrt.getch

        except ImportError:
            # for POSIX-based systems (with termios & tty support)
            import tty, sys, termios # raises ImportError if unsupported

            def _ttyRead():
                fd = sys.stdin.fileno()
                oldSettings = termios.tcgetattr(fd)

                try:
                    tty.setcbreak(fd)
                    answer = sys.stdin.read(1)
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, oldSettings)

                return answer

            getChar._func=_ttyRead

    return getChar._func()

class Agilis(Device, ProcessHandler):
    def __init__(self, port, name = 'agilis', parent = None, connect = False):
        self.mirrors = [1]
        if parent is not None:
            Device.__init__(self, name, parent = parent)
            ProcessHandler.__init__(self)
            self.zero = {}
            for mirror in self.mirrors:
                for knob in ['X%i'%mirror, 'Y%i'%mirror]:
                    self.add_knob(knob)
        self.port = port
        self._connected = 0
        if connect:
            self._connected = self._connect()
        self.mirror=None
        self.range = {'X1':377150, 'Y1':310100}

    def _connect(self):
        self.serial = serial.Serial(port = self.port, baudrate = 921600, parity = ser.PARITY_NONE, stopbits = ser.STOPBITS_ONE, bytesize = ser.EIGHTBITS, timeout = 1, encoding = 'ascii', name = 'Agilis')
        if self.serial._connected:
            self.command('RS')
            self.command('MR')
            self.saved_positions = {}
            self._connected = 1
            self.step_size = 50
            for mirror in self.mirrors:
                self.set_channel(mirror)
                for axis in [1,2]:
                    self.command('%sSU+%i'%(axis, self.step_size))
                    self.command('%sSU-%i'%(axis, self.step_size))
            self.set_channel(1)

    def _actuate(self, state):
        ''' Software-based absolute positioning, achieved by moving relative to a known last position '''
        ''' Pass in a value from -1 to 1 for each axis; autoscaling to calibrated range is done before
            actuation '''
        if self.range == {}:
            return
        indices = {'X1':0, 'Y1':1, 'X2':2, 'Y2':3}
        for knob in state:
            index = indices[knob]
            mirror = int(knob[1])
            axis = {'X':1,'Y':2}[knob[0]]
            if self.state[knob] is None:
                self.state[knob] = state[knob]
            step = state[knob] - self.state[knob]
            unnorm_step = step/2 * (1+self.range[knob]/self.step_size)
            if step != 0:
                self.relative_move(mirror, axis, unnorm_step)
                print('step:', step, 'unnorm_step:', unnorm_step)
        self.wait_until_stopped(axis)
    def clear_buffer(self):
        time.sleep(.1)
        while True:
            if self.serial.read() == '':
                break

    def calibrate(self):
        for mirror in self.mirrors:
            self.set_channel(mirror)
            for axis in [1,2]:
                try:
                    self.clear_buffer()
                    self.command('%sMV-3'%axis)     # move to negative limit
                    self.wait_until_stopped(axis)
                    self.clear_buffer()
                    self.command('%sZP'%axis)   # clear step counter
                    self.command('%sPR100'%axis)    # move 100 steps out of limit
                    self.wait_until_stopped(axis)
                    self.command('%sMV3'%axis)  # move to positive limit
                    self.wait_until_stopped(axis)
                    try:
                        check_steps = self.command('%sTP?'%axis)
                        steps = int(check_steps.split('%sTP'%axis)[1])
                    except:
                        self.clear_buffer()
                        check_steps = self.command('%sTP?'%axis)
                        steps = int(check_steps.split('%sTP'%axis)[1])
                    axis_range = self.step_size*steps
                    self.axis_label = {1:'X',2:'Y'}[axis]
                    self.label = self.axis_label + str(mirror)
                    self.range[self.label] = axis_range
                    print('Measured axis range: %f'%axis_range)
                    steps_to_zero = int(axis_range/2/self.step_size)
                    self.command('%sPR%i'%(axis,-steps_to_zero))
                    self.wait_until_stopped(axis)
                    self.clear_buffer()
                except Exception as e:
                    print(e)
                    print(self.command('TE?'))
        target_parent_state = {self.name:{}}
        for knob in self.state:
            self.state[knob] = 0
            self.parent.state[self.name][knob] = 0
            target_parent_state[self.name][knob] = 0
        self.parent.actuate(target_parent_state)

    def command(self, cmd, reply = True):
        r = self.serial.command(cmd, suffix = '\r\n', reply = reply)
        if reply:
            return r.split('\r')[0]

    def cost(self, num = 1):
        vals = []
        for i in range(num):
            vals.append(self.labjack.AIn(0))
        return np.mean(vals)

    def relative_move(self, mirror, axis, step=100):
        self.set_channel(mirror)
        self.command('%iPR%i'%(axis, step), reply = False)

    def set_channel(self, mirror):
        if self.mirror != mirror:
            while True:
                self.command('CC%i'%mirror)
                actual = self.command('CC?')
                if int(actual[2]) == mirror:
                    break
        self.mirror = mirror

    def get_position(self, mirror, axis=None):
        ''' If type(mirror)==int, returns the position of a target mirror and axis.
            If mirror=='all', queries all axes and returns an 8-element array. '''
        if type(mirror) == int:
            self.set_channel(mirror)
            self.command('%iMA'%axis, reply = False)
            while True:
                r = self.serial.read()
                if r != '':
                    return (r.split('1MA')[1].split('\r')[0])

        elif mirror == 'all':
            pos = []
            for mirror in self.mirrors:
                for axis in [1, 2]:
                    pos.append(self.get_position(mirror, axis))
            return pos

    def wait_until_stopped(self, axis):
        while True:
            if self.command('%iTS?'%axis) == '%iTS0'%axis:
                return

    def set_position(self, mirror, axis, position):
        if type(position) == int:
            self.set_channel(mirror)
            self.command('%iPA%i'%(axis, position))
        elif type(position) == list:
            i = 0
            for mirror in self.mirrors:
                self.set_channel(mirror)
                for axis in [1,2]:
                    self.set_position(mirror, axis, position[i], reply = False)

    def save_position(self, index):
        ''' Saves the position of one more more axes in an 8-element list.
            Unsaved axes are written as -1 '''
        self.saved_positions[index] = self.get_position(mirror='all')

    def walk(self):
        self._run_thread(self.walk_thread, stoppable = False)

    def walk_thread(self):
        print('Entering walk mode.')
        step = .05
        while True:
            sign = None
            command = getChar().decode('ASCII')
            if command.lower() in ['q', 'quit', 'exit']:
                break
            elif command == 'b':
                step *= 2
                print('Increasing step')

            elif command == 'v':
                step /= 2
                print('Decreasing step')

            elif command == 'j':
                knob = 'X1'
                sign = 1
                # self.relative_move(1, 1, step = step)
            elif command == 'l':
                # self.relative_move(1, 1, step = -step)
                knob = 'X1'
                sign = -1
            elif command == 'k':
                knob = 'Y1'
                sign = -1
                # self.relative_move(1, 2, step = -step)
            elif command == 'i':
                knob = 'Y1'
                sign = 1
                # self.relative_move(1, 2, step = step)
            elif command == 'd':
                knob = 'X2'
                sign = -1
                # self.relative_move(2, 1, step = -step)
            elif command == 'a':
                knob = 'X2'
                sign = 1
                # self.relative_move(2, 1, step = step)
            elif command == 's':
                knob = 'Y2'
                sign = -1
                # self.relative_move(2, 2, step = -step)
            elif command == 'w':
                knob = 'Y2'
                sign = 1
                # self.relative_move(2, 2, step = step)
            if sign is not None:
                self.parent.actuate({self.name:{knob:self.state[knob]+sign*step}})

    def zero(self):
        for mirror in [1,2]:
            for axis in [1,2]:
                self.set_position(mirror, axis, 500)

if __name__ == '__main__':
    m = Agilis(port='COM15',connect=True)
