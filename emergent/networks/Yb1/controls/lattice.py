from emergent.archetypes.node import Control
from utility import experiment, extract_pulses
import numpy as np
import time

class Lattice(Control):
    def __init__(self, name, parent = None, path='.'):
        super().__init__(name, parent = parent, path=path)
        self.signal_threshold_in_mV = 100

    def add_labjack(self, labjack):
        self.labjack = labjack
        self.labjack.prepare_streamburst(channel=0, trigger = 0)

    @experiment
    def load_lattice(self, state):
        ''' Actuates to a new state, waits for TTL high on FIO0, measures a signal, extracts pulses, and returns difference between ground and background populations. '''
        self.actuate(state)
        ground, background, excited = state_readout(duration=0.1)

        return -(ground-background)

    def state_readout(self, duration = 0.1):
        signal = self.labjack.streamburst(duration)           # measure three pulses
        pulses = extract_pulses(signal, self.signal_threshold_in_mV/1000)
        ground = np.max(pulses[0])
        background = np.max(pulses[1])
        excited = np.max(pulses[2])

        return ground, background, excited

    @experiment
    def lattice_ratio(self, state):
        ''' Evaluates lattice loading efficiency by interleaving between green and lattice loading. '''
        self.actuate(state)

        while True:
            mode = {0:'green', 1:'lattice'}[self.labjack.DIn(1)]        # interleave between measuring green and lattice
            if mode is 'green':
                break

        ''' Measure fluorescence from green loading '''
        ground, background, excited = state_readout(duration=0.1)
        green_count = ground-background

        ''' Measure fluorescence from lattice loading '''
        ground, background, excited = state_readout(duration=0.1)
        lattice_count = ground-background

        return -lattice_count/green_count
