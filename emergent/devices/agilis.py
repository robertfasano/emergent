import sys
import os
import numpy as np
from emergent.protocols import serial
import serial as ser
from emergent.archetypes.node import Device
from emergent.utility import getChar
import time

class Agilis(Device):
    def __init__(self, port, name = 'agilis', parent = None, connect = False):
        if parent is not None:
            Device.__init__(self, name, parent = parent)
            self.zero = {}
            for input in ['X1','Y1','X2','Y2']:
                self.add_input(input)
                self.zero[input] = self.children[input].state
                if self.zero[input] is None:
                    self.zero[input] = 0
        self.port = port
        self._connected = 0
        if connect:
            self._connected = self._connect()
        self.mirror=None
        self.range = {'X1':377150, 'Y1':310100, 'X2':250800, 'Y2':250550}

    def _connect(self):
        self.serial = serial.Serial(port = self.port, baudrate = 921600, parity = ser.PARITY_NONE, stopbits = ser.STOPBITS_ONE, bytesize = ser.EIGHTBITS, timeout = 1, encoding = 'ascii', name = 'Agilis')
        if self.serial._connected:
            self.command('RS')
            self.command('MR')
            self.saved_positions = {}
            self.mirrors = [1,2]
            self._connected = 1
            self.step_size = 50
            for mirror in [1,2]:
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
        for input in state:
            index = indices[input]
            mirror = int(input[1])
            axis = {'X':1,'Y':2}[input[0]]

            step = state[input] - self.state[input]
            unnorm_step = step/2 * (1+self.range[input]/self.step_size)
            if step != 0:
                self.relative_move(mirror, axis, unnorm_step)
                print('step:', step, 'unnorm_step:', unnorm_step)

    def clear_buffer(self):
        time.sleep(.1)
        while True:
            if self.serial.read() == '':
                break

    def calibrate(self):
        for mirror in [1,2]:
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
        for input in self.state:
            self.state[input] = 0

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
        print('Entering walk mode.')
        step = 100

        while True:
            command = getChar().decode('ASCII')
            if command.lower() in ['q', 'quit', 'exit']:
                break
            elif command == 'b':
                step *= 2
                print('Increasing step')

            elif command == 'v':
                step /= 2
                print('Decreasing step')

            elif command == 's':
                self.relative_move(1, 1, step = step)
            elif command == 'w':
                self.relative_move(1, 1, step = -step)
            elif command == 'a':
                self.relative_move(1, 2, step = -step)
            elif command == 'd':
                self.relative_move(1, 2, step = step)
            elif command == 'k':
                self.relative_move(2, 1, step = -step)
            elif command == 'i':
                self.relative_move(2, 1, step = step)
            elif command == 'l':
                self.relative_move(2, 2, step = -step)
            elif command == 'j':
                self.relative_move(2, 2, step = step)

    def zero(self):
        for mirror in [1,2]:
            for axis in [1,2]:
                self.set_position(mirror, axis, 500)

if __name__ == '__main__':
    m = Agilis(port='COM15',connect=True)