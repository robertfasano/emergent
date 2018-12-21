import numpy as np
from emergent.signals import WatchdogSignal
import logging as log
from emergent.modules import Sampler, recommender, ProcessHandler

class Watchdog(ProcessHandler):
    def __init__(self, parent, name = 'watchdog'):
        super().__init__()
        self.parent = parent
        self.name = name
        self.threshold_type = 'lower'
        self.threshold = 1
        self.value = 0
        self.state = 0
        self.signal = WatchdogSignal()
        self.enabled = True
        self.reacting = False

    def check(self):
        ''' Private method which calls self.measure then updates the state '''
        value = self.measure()
        if self.threshold_type == 'upper':
            self.state = value < self.threshold
        elif self.threshold_type == 'lower':
            self.state = value > self.threshold
        self.signal.emit(self.state)
        if not self.state:
            log.info('Watchdog %s is reacting to an unlock!'%self.name)
            self._run_thread(self.react, stoppable=False)
        return self.state

    def measure(self):
        return

    def react(self):
        return

    def reoptimize(self, state, experiment_name):
        self.enabled = False
        self.reacting = True
        self.parent.optimize(state, experiment_name, threaded = False, priority = True)
        self.enabled = True
        self.reacting = False


if __name__ == '__main__':
    w = Watchdog()
