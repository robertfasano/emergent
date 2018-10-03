from emergent.archetypes.node import Device
import logging as log
import numpy as np
import time

class Ramp(Device):
    def __init__(self, name, duration, labjack, type = {0:'constant',1:'constant'}, parent = None, steps = 1000, trigger = None):
        super().__init__(name=name, parent = parent)
        self.duration = duration
        self.labjack = labjack
        self.steps = steps
        self.type = type
        for ch in self.type:
            if self.type[ch] is 'constant':
                self.add_input('DAC%i: Constant V0'%ch)
            if self.type[ch] is 'linear':
                self.add_input('DAC%i: Linear V0'%ch)
                self.add_input('DAC%i: Linear Vf'%ch)
            elif self.type[ch] is 'exponential':
                self.add_input('DAC%i: Exponential V0'%ch)
                self.add_input('DAC%i: Exponential tau'%ch)
        channels = ['DAC%i'%i for i in self.type]
        self.labjack.prepare_stream_out(trigger=trigger)
        self.initialized = 0

    def _actuate(self, state):
        state = self.get_missing_keys(state, None)
        if self.initialized:
            t = np.linspace(0,self.duration, 1000)
            y = np.zeros((len(t),len(self.type)))
            for ch in self.type:
                if self.type[ch] is 'constant':
                    y[:,ch] = state['DAC%i: Constant V0'%ch]
                elif self.type[ch] is 'linear':
                    slope = (state['DAC%i: Linear Vf'%ch]-state['DAC%i: Linear V0'%ch])/self.duration
                    y[:,ch] = state['DAC%i: Linear V0'%ch] + slope*t
                elif self.type[ch] is 'exponential':
                    y[:,ch] = state['DAC%i: Exponential V0'%ch]*np.exp(-t/state['DAC%i: Exponential tau'%ch])
            sequence, scanRate = self.labjack.resample(y, self.duration, max_samples = self.steps)
            self.labjack.stream_out(list(self.type.keys()), sequence, scanRate, loop=0)
        else:
            self.initialized = 1

    def _connect(self):
        return self.labjack._connected
