import numpy as np
from emergent.signals import WatchdogSignal
import logging as log
from emergent.modules import Sampler, recommender

class Watchdog():
    def __init__(self, parent, name = 'watchdog'):
        self.parent = parent
        self.name = name
        self.threshold_type = 'lower'
        self.threshold = 1
        self.value = 0
        self.state = 0
        self.signal = WatchdogSignal()
        self.enabled = True

    def check(self):
        ''' Private method which calls self.measure then updates the state '''
        value = self.measure()
        if self.threshold_type == 'upper':
            self.state = value < self.threshold
        elif self.threshold_type == 'lower':
            self.state = value > self.threshold
        if not self.state:
            log.info('Watchdog %s is reacting to an unlock!'%self.name)
            self.parent.manager._run_thread(self.react, stoppable=False)
        else:
            log.info('Watchdog %s is happy!'%self.name)

        self.signal.emit(self.state)

        return self.state

    def measure(self):
        return

    def react(self):
        return

    def reoptimize(self, state, experiment_name):
        self.enabled = False
        self.parent.optimize(state, experiment_name, threaded = False)
        self.enabled = True
        self.check()


if __name__ == '__main__':
    w = Watchdog()
