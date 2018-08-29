import sys
import os
import numpy as np
from emergent.protocols import serial
import serial as ser
from emergent.archetypes.node import Device
from emergent.utility import getChar()


class Agilis(Device):
    def __init__(self, port, name = 'agilis', parent = None):
        Device.__init__(self, name, parent = parent)
        self.port = port
        self._connected = 0
        for input in ['X1','Y1','X2','Y2']:
            self.add_input(input)

    def _connect(self):
        self.serial = serial.Serial(port = self.port, baudrate = 921600, parity = ser.PARITY_NONE, stopbits = ser.STOPBITS_ONE, bytesize = ser.EIGHTBITS, timeout = 1, encoding = 'ascii', name = 'Agilis')
        if self.serial._connected:
            self.command('MR')
            self.saved_positions = {}
            self.mirrors = [1,2]
            self.mirror = 1
            self.position = np.zeros(len(2*self.mirrors))
            self._connected = 1

    def _actuate(self, state):
        ''' Software-based absolute positioning, achieved by moving relative to a known last position '''
        indices = {'X1':0, 'Y1':1, 'X2':2, 'Y2':3}
        for input in state:
            index = indices[input]
            mirror = input[1]-1
            step = state[input] - self.state[input]
            if step != 0:
                self.relative_move(mirror, axis, step)

    def command(self, cmd, reply = True):
        self.serial.command(cmd, suffix = '\r\n', reply = reply)

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
            self.command('CC%i'%mirror)
        self.mirror = mirror

    def get_position(self, mirror, axis = None):
        ''' If type(mirror)==int, returns the position of a target mirror and axis.
            If mirror=='all', queries all axes and returns an 8-element array. '''
        if type(mirror) == int:
            self.set_channel(mirror)
            return self.command('%iMA'%axis)
        elif mirror == 'all':
            pos = []
            for mirror in self.mirrors:
                for axis in [1, 2]:
                    pos.append(self.get_position(mirror, axis))
            return pos

    def set_position(self, mirror, axis, position):
        self.position = position
        if type(position) == int:
            self.set_channel(mirror)
            self.command('%iPA%i'%(axis, position), reply = False)
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


            elif command == 'a':
                self.relative_move(1, 1, step = step)
            elif command == 'd':
                self.relative_move(1, 1, step = -step)
            elif command == 's':
                self.relative_move(1, 2, step = -step)
            elif command == 'w':
                self.relative_move(1, 2, step = step)
            elif command == 'j':
                self.relative_move(2, 1, step = -step)
            elif command == 'l':
                self.relative_move(2, 1, step = step)
            elif command == 'k':
                self.relative_move(2, 2, step = -step)
            elif command == 'i':
                self.relative_move(2, 2, step = step)


if __name__ == '__main__':
    m = Agilis(port='COM15')
#    m.walk()
