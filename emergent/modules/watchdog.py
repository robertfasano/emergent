import numpy as np
from emergent.signals import WatchdogSignal
import logging as log
from emergent.modules import Sampler, recommender, ProcessHandler

class Watchdog(ProcessHandler):
    def __init__(self, parent, experiment, threshold, input_state = None, name = 'watchdog'):
        super().__init__()
        self.parent = parent
        self.experiment = experiment        # experiment to run to check lock state
        self.threshold = threshold
        self.input_state = input_state
        if self.input_state is None:
            self.input_state = parent.state
        self.name = name

        self.threshold_type = 'lower'
        self.value = 0
        self.state = 0
        self.signal = WatchdogSignal()
        self.enabled = True
        self.reacting = False

        ''' Set up sampler object '''
        experiment_params = recommender.load_experiment_parameters(self.parent, experiment.__name__)
        self.sampler = Sampler('Watchdog',
                          self.input_state,
                          self.parent,
                          self.experiment,
                          experiment_params)
        self.sampler.skip_lock_check = True

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
        return -self.sampler._cost(self.parent.state)

    def react(self):
        self.confirm_lock()

    def confirm_lock(self):
        return

    def reoptimize(self, state, experiment_name):
        self.enabled = False
        self.reacting = True
        self.parent.optimize(state, experiment_name, threaded = False, skip_lock_check = True)
        self.enabled = True
        self.reacting = False


if __name__ == '__main__':
    w = Watchdog()
