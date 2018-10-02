from emergent.archetypes.node import Device
import logging as log
import numpy as np
import time

class Ramp(Device):
    def __init__(self, name, duration, labjack, type = 'linear', parent = None, steps = 1000, trigger = None):
        super().__init__(name=name, parent = parent)
        self.duration = duration
        self.labjack = labjack
        self.steps = steps
        self.type = type
        if type is 'linear':
            self.add_input('V0')
            self.add_input('Vf')
        elif type is 'exponential':
            self.add_input('V0')
            self.add_input('tau')
        self.labjack.prepare_stream_out(['DAC0'], trigger=trigger)
        self.initialized = 0

    def _actuate(self, state):
        state = self.get_missing_keys(state, None)
        if self.initialized:
            t = np.linspace(0,self.duration, 1000)
            if self.type is 'linear':
                slope = (state['Vf']-state['V0'])/self.duration
                y = state['V0'] + slope*t
            elif self.type is 'exponential':
                y = state['V0']*np.exp(-t/state['tau'])
            sequence, scanRate = self.labjack.resample(y, self.duration, max_samples = self.steps)
            self.labjack.stream_out([0], sequence, scanRate, loop=0)
        else:
            self.initialized = 1

    def _connect(self):
        return self.labjack._connected
