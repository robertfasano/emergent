from labAPI.devices.labjackT7 import LabJack
import numpy as np

class PMT():
    def __init__(self, labjack = None):
        if labjack == None:
            labjack = LabJack()
        self.labjack = labjack
        self.labjack.AOut(3,-5, HV=True)
        self.labjack.AOut(2,5, HV=True)
        self.labjack.AOut(1,.5)
    def read(self, num):
        vals = []
        for i in range(num):
            vals.append(self.labjack.AIn(0))
        return np.mean(vals)
    
    
if __name__ == '__main__':
    pmt = PMT()