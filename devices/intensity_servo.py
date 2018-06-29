import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-2]))
from labAPI.devices.labjackT7 import LabJack
import numpy as np
from labAPI.archetypes.device import Device

class IntensityServo(Device):
    def __init__(self, connect = False, parent = None, labjack = None):
        super().__init__(name='intensity_servo', parent = parent)
        self._connected = 0
        if labjack == None:
            labjack = LabJack('470016970')
        self.labjack = labjack
        if connect:
            self._connect()

    def _connect(self):
        if self.labjack._connected:
            self.actuate([3,3])
            self._connected = 1

    def actuate(self, state):
        ''' state[0] corresponds to slowing, [1] to cooling '''
        self.set_setpoint('slowing', state[0])
        self.set_setpoint('cooling', state[1])
        self.state = state

    def set_setpoint(self, target, value):
        self.labjack.AOut({'slowing':0, 'cooling':1}[target], value, prefix = 'FIO')

if __name__ == '__main__':
    pmt = PMT(labjack=None)
