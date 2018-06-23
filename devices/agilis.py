import sys
import os
import numpy as np
#"piezos... singing the song of their people" - Wes
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-2]))  
from labAPI.protocols import serial
import serial as ser
import msvcrt
from labAPI.algorithms.align import Aligner
from labAPI.devices.labjackT7 import LabJack
from labAPI.archetypes.device import Device

class NewportPiezo(Device, Aligner):
    def __init__(self, name, port):
        super().__init__(name)
        self.serial = serial.Serial(port = port, baudrate = 921600, parity = ser.PARITY_NONE, stopbits = ser.STOPBITS_ONE, bytesize = ser.EIGHTBITS, timeout = 1, encoding = 'ascii')
        self.command('MR')
        self.labjack = LabJack(devid='470016973')
        self.saved_positions = {}
        self.mirrors = [1,2]
        self.mirror = 1
        self.position = np.zeros(len(2*self.mirrors))
        
    def actuate(self, pos):
        ''' Software-based absolute positioning, achieved by moving relative to a known last position '''
        for mirror in self.mirrors:
            self.set_channel(mirror)
            for axis in [1,2]:
                step = pos[mirror+axis-1]-self.position[mirror+axis-1]
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
        self.position[mirror+axis-1] += step
        
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
    #    name = 'mirror'
    #    other_name = 'mirror'
        
    #    if mirror == 1: 
    #        name = 'input'
    #        other_name = 'output'
    #    elif mirror == 2: 
    #        name = 'output'
    #        other_name = 'input'
        print('Entering walk mode.')
        #print('Controlling %s alignment. Type \'5\' to switch to %s or \'q\' to quit'%(name, other_name) )
        # Open control console
        step = 100

        while True:
            command = msvcrt.getch().decode('ASCII')
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
    m = NewportPiezo(port='COM15')
#    m.walk()
        