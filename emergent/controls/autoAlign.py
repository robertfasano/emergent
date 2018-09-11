import time
from emergent.devices.labjackT7 import LabJack
from emergent.archetypes.node import Control
import numpy as np
import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-1]))
from utility import cost
import datetime

class AutoAlign(Control):
    ''' Control node for automated fiber alignment. A Labjack T7 is used both for
        MEMS mirror actuation via SPI and for measurement of the transmitted power. '''
    def __init__(self, name, labjack, parent = None, path='.'):
        super().__init__(name, parent = parent, path=path)
        self.labjack = labjack
        self.options = {'optimize':self.optimize}
    def readADC(self, num = 10, delay = 0):
        ''' Reads the transmitted power from Labjack channel AIN0 with an optional
            delay. num samplings can be averaged together to improve the signal to
            noise. '''
        time.sleep(delay)
        return self.labjack.AIn(0, num=num)

    @cost
    def measure_power(self, state):
        ''' Moves to the target alignment and measures the transmitted power. '''
        self.actuate(state)
        cost = -self.readADC()
        t = datetime.datetime.now()
        for name in self.inputs['MEMS']:
            input = self.inputs['MEMS'][name]
            self.update_dataframe(t, 'MEMS', name, input.state)
        self.update_cost(t, cost)
        return cost

    def optimize(self):
        state = self.get_substate(['MEMS.X','MEMS.Y'])
        params = {'plot':0, 'tol':4e-3}
        self.optimizer.simplex(state, self.measure_power, params)
