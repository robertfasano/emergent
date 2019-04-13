from emergent.core import Hub
from emergent.utilities.decorators import experiment, trigger
import numpy as np
import time

def extract_pulses(data, threshold):
    ''' Splits a numpy array into segments which are above a threshold. '''
    data = np.array(data)
    return np.split(data, np.where(np.diff(data > threshold))[0] + 1)[1::2]


class Lattice(Hub):
    def __init__(self, name, addr = None, network = None):
        super().__init__(name, addr, network)
        self.signal_threshold_in_mV = 100
        self.max_samples = 1000
        self.trigger_channel = 4

        self.ignored = ['labjack']          # add the names of any unpicklable attributes here
    @trigger
    def trigger(self):
        ''' Wait until TTL low, then return as soon as TTL high is detected '''
        while self.labjack.DIn(self.trigger_channel):
            continue
        while not self.labjack.DIn(self.trigger_channel):
            continue
        return True

    @experiment
    def monitor(self, state, params = {}):
        ''' A dummy experiment for standalone monitoring. '''
        print('sync')

        return self.labjack.DIn(self.trigger_channel)

    @experiment
    def load_lattice(self, state):
        ''' Actuates to a new state, waits for TTL high on FIO0, measures a signal, extracts pulses, and returns difference between ground and background populations. '''
        self.actuate(state)
        ground, background, excited = self.state_readout(duration=0.07)
        return -(ground-background)

    def state_readout(self, duration = 0.1):
        signal = self.ljIN.streamburst(duration, max_samples = self.max_samples)           # measure three pulses
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
        ground, background, excited = self.state_readout(duration=0.07)
        green_count = ground-background

        ''' Measure fluorescence from lattice loading '''
        ground, background, excited = self.state_readout(duration=0.07)
        lattice_count = ground-background

        return -lattice_count/green_count
