import time
from emergent.things.labjack import LabJack
from emergent.core import Hub
import numpy as np
import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-1]))
from emergent.utilities.decorators import experiment
import datetime

class AutoAlign(Hub):
    ''' Hub for automated fiber alignment. A Labjack T7 is used both for
        MEMS mirror actuation via SPI and for measurement of the transmitted power. '''
    def __init__(self, name, labjack, parent = None, network = None):
        super().__init__(name, parent = parent, core = core)
        self.labjack = labjack

    def readADC(self, num = 10, delay = 0):
        ''' Reads the transmitted power from Labjack channel AIN0 with an optional
            delay. num samplings can be averaged together to improve the signal to
            noise. '''
        time.sleep(delay)
        return self.labjack.AIn(0, num=num)

    @experiment
    def measure_power(self, state, params = {}):
        ''' Moves to the target alignment and measures the transmitted power. '''
        self.actuate(state)
        cost = -self.readADC()
        return cost
