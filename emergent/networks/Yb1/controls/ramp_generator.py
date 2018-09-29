from emergent.archetypes.node import Device
import logging as log
import numpy as np

class IntensityRamp(Device):
    def __init__(self, name, duration, labjack, parent = None):
        super().__init__(name=name, parent = parent)
        self.duration = duration
        self.labjack = labjack
        self.add_input('point1')
        self.add_input('point2')
        self.prepare_stream_out()
        self.initialized = 0

    def _actuate(self, state):
        state = self.get_missing_keys(state, None)
        if self.initialized:
            slope = (state['point2']-state['point1'])/self.duration
            t = np.linspace(0,self.duration, 100)
            y = state['point1'] + slope*t
            sequence, scanRate = self.labjack.resample(y, self.duration, max_samples = 100)
            self.labjack.stream_out([0], sequence, scanRate, trigger=1)
            self.labjack.stream_stop()
            self.labjack.prepare_streamburst(channel=0, trigger = 0)
        else:
            self.initialized = 1

    def _connect(self):
        return 1
