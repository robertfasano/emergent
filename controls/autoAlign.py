'''if the amplifiers are not working, then first unplug and reinsert the #1 +5V HV the pin once it is connected
and initialized; otherwise, ensure that 5 volts of power are being delivered to the board'''
import time
from devices.labjackT7 import LabJack
from archetypes.node import Control
import numpy as np
import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-1]))

def cost(func):
    return func

class AutoAlign(Control):
    def __init__(self, name, labjack, parent = None, path='.'):
        super().__init__(name, parent = parent, path=path)
        self.labjack = labjack

    def readADC(self, num = 1, delay = 0):
        time.sleep(delay)
        return self.labjack.AIn(0, num=num)

    @cost
    def measure_power(self, state):
        self.actuate(state)
        return self.readADC()
