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
    def __init__(self, state, bounds, experiment, params, trigger = None):
        ''' Initialize the sampler and link to the parent Hub. '''
        self.state = state
        self.bounds = bounds
        self.scaler = Scaler(self.state, self.bounds)
        self.trigger = None
        if trigger is not None:
            self.trigger = getattr(self.hub, settings['process']['trigger'])


        self.experiment = experiment
        self.experiment_params = params

    def measure(self, state, norm=True):
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
