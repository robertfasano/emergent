import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-2]))
#from labAPI.devices.labjackT7 import LabJack
import numpy as np
#import labAPI.archetypes.device as device
from labAPI.archetypes.device import Device

class PMT(Device):
    def __init__(self, labjack = None):
        super().__init__(name='PMT')
        
        if labjack == None:
            labjack = LabJack(self.id)
        self.labjack = labjack
        self.labjack.AOut(3,-5, HV=True)
        self.labjack.AOut(2,5, HV=True)
        self.labjack.AOut(1,pmt.params['gain']['value'])
        
    def read(self, num):
        vals = []
        for i in range(num):
            vals.append(self.labjack.AIn(0))
        return np.mean(vals)
    
    
if __name__ == '__main__':
    pmt = PMT(labjack=None)