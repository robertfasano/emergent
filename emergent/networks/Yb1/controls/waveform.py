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
        self.all_inputs = {'constant':['Constant V0'], 'linear': ['Linear V0', 'Linear Vf'], 'exponential':['Exponential V0', 'Exponential tau']}
        for ch in self.type:
            self.add_ramp_type_inputs(ch)
        channels = ['DAC%i'%i for i in self.type]
        self.labjack.prepare_stream_out(trigger=trigger)
        self.initialized = 0

        for channel in ['DAC0', 'DAC1']:
            for type in self.all_inputs:
                self.options[channel+': '+type] = getattr(self,channel+'_'+type)

    def add_ramp_type_inputs(self, ch):
        inputs = self.all_inputs[self.type[ch]]
        for input in inputs:
            self.add_input('DAC%i: %s'%(ch, input))

    def delete_ramp_type_inputs(self, ch):
        current_inputs = list(self.children.keys())
        for input in current_inputs:
            if 'DAC%i'%ch in input:
                self.remove_input(input)

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

    def switch_type(self, ch, new_type):
        if self.type is new_type:
            return
        self.delete_ramp_type_inputs(ch)
        self.type[ch] = new_type
        self.add_ramp_type_inputs(ch)
        self.parent.actuate(self.parent.state)
        log.warn('State sync conflict resolved.')

    def DAC0_constant(self):
        self.switch_type(0, 'constant')

    def DAC1_constant(self):
        self.switch_type(1, 'constant')

    def DAC0_linear(self):
        self.switch_type(0, 'linear')

    def DAC1_linear(self):
        self.switch_type(1, 'linear')

    def DAC0_exponential(self):
        self.switch_type(0, 'exponential')

    def DAC1_exponential(self):
        self.switch_type(1, 'exponential')
