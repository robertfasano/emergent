from emergent.archetypes.node import Device
import logging as log
import numpy as np
import time

class LinearRamp(Device):
    def __init__(self, name, duration, labjack, parent = None):
        super().__init__(name=name, parent = parent)
        self.duration = duration
        self.labjack = labjack
        self.add_input('V0')
        self.add_input('Vf')
        self.labjack.prepare_stream_out(['DAC0'], trigger=0)
        self.initialized = 0

    def _actuate(self, state):
        state = self.get_missing_keys(state, None)
        if self.initialized:
            slope = (state['Vf']-state['V0'])/self.duration
            t = np.linspace(0,self.duration, 100)
            y = state['V0'] + slope*t
            sequence, scanRate = self.labjack.resample(y, self.duration, max_samples = 500)
            self.labjack.stream_out([0], sequence, scanRate, loop=0)
        else:
            self.initialized = 1

    def test(self):
        sequence, scanRate = self.labjack.resample([0,1], 0.5, max_samples = 500)
        for i in range(n):
            self.labjack.stream_out([0], sequence, scanRate, loop=0)
    def _connect(self):
        return 1
