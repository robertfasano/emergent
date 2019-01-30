from emergent.modules import Hub
from utility import experiment, extract_pulses, trigger, error
import numpy as np
import time

class Photoassociation(Hub):
    def __init__(self, name, addr = None, network = None):
        super().__init__(name = name, addr = addr, network = network)
        self.signal_threshold_in_mV = 100
        self.max_samples = 1000
        self.trigger_channel = 4

        self.ignored = ['labjack']          # add the names of any unpicklable attributes here

    @error
    def loop_filter_output(self, state, params={'wait': 0.1}):
        self.actuate(state)
        time.sleep(params['wait'])
        return self.labjack.AIn(0)
