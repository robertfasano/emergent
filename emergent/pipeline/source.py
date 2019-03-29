''' The Sampler module serves as an interface between the real parameter space of the
    experiment and the normalized space used by optimization algorithms. Experiments
    are run by instantiating a Sampler with the desired parameters, then either
    repeatedly executing Sampler._cost (for simple continuous measurement) or
    passing the Sampler into an Algorithm instance for optimization. '''

import itertools
import pickle
import time
import pandas as pd
import numpy as np
import datetime
import logging as log
from emergent.utilities import recommender
from emergent.modules.scaler import Scaler

class Source():
    ''' General methods '''
    def __init__(self, name, settings):
        ''' Initialize the sampler and link to the parent Hub. '''
        self.name = name


        self.state = settings['state']
        self.hub = settings['hub']
        self.limits = settings['range']
        self.scaler = Scaler(self.state, self.limits)
        self.trigger = None
        if 'trigger' in settings['process']:
            self.trigger = getattr(self.hub, settings['process']['trigger'])


        self.experiment = getattr(self.hub, settings['experiment']['name'])
        self.experiment_params = settings['experiment']['params']

        self.skip_lock_check = False           # if True, experiments will disregard watchdog state

        self.prepare(self.state)

    ''' Logistics functions '''
    def _cost(self, state, norm=True):
        ''' Converts the array back to the form of d,
            unnormalizes it, and returns cost evaluated on the result. '''
        if type(state) is np.ndarray:
            norm_target = self.scaler.array2state(state)
        else:
            norm_target = state
        if norm:
            target = self.scaler.unnormalize(norm_target)
        else:
            target = norm_target
        if not self.skip_lock_check:
            self.hub._check_lock()

        results = []
        if 'cycles per sample' not in self.experiment_params:
            self.experiment_params['cycles per sample'] = 1
        for i in range(int(self.experiment_params['cycles per sample'])):
            if self.trigger is not None:
                self.trigger()
            c = self.experiment(target, self.experiment_params)
            results.append(c)

        c = np.mean(results)
        error = None
        if len(results) > 1:
            error = np.std(results)/np.sqrt(len(results))

        return c

    def save(self, filename):
        ''' Byte-serialize the sampler and all attached picklable objects and
            save to file. '''
        self.history.to_csv(self.hub.network.path['data']+filename+'.csv')
        self.hub.macro_buffer.add(self.hub.state)
        try:
            with open(self.hub.network.path['data']+'%s.sci'%filename, 'wb') as file:
                pickle.dump(self, file)
        except Exception as e:
            log.warning('Could not pickle Sampler state:', e)
