import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-2]))
from labAPI.devices.labjackT7 import LabJack
import numpy as np
from labAPI.archetypes.device import Device

class PMT(Device):
    def __init__(self, connect = False, parent = None, labjack = None):
        super().__init__(name='PMT', parent = parent)
        self._connected = 0
        if labjack == None:
            labjack = LabJack('470016970')
        self.labjack = labjack
        if connect:
            self._connect()

    def _connect(self):
        if self.labjack._connected:
            self.labjack.AOut(3,-5, HV=True)
            self.labjack.AOut(2,5, HV=True)
            self.labjack.AOut(1,self.params['gain']['value'])
            self._connected = 1
            
    def read(self, num):
        vals = []
        for i in range(num):
            vals.append(self.labjack.AIn(0))
        return np.mean(vals)
    
    def set_gain(self, value):
        self.params['gain']['value'] = value
        self.labjack.AOut(1,value)
    
    
if __name__ == '__main__':
    pmt = PMT(labjack=None)