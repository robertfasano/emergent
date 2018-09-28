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
        signal = self.labjack.streamburst(.1)           # measure three pulses

        pulses = extract_pulses(signal, self.signal_threshold_in_mV/1000)
        ground = np.max(pulses[0])
        background = np.max(pulses[1])
        excited = np.max(pulses[2])

        return -(ground-background)
