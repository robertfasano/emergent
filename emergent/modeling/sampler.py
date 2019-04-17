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
import uuid
from emergent.utilities import recommender
from emergent.modeling.scaler import Scaler
from emergent.utilities.decorators import thread

class Sampler():
    ''' General methods '''
    def __init__(self, name, settings, t=None):
        ''' Initialize the sampler and link to the parent Hub. '''
        self.name = name
        self.id = str(uuid.uuid1())

        if t is None:
            t = datetime.datetime.now().strftime('%Y%m%dT%H%M')
        self.state = settings['state']
        self.hub = settings['hub']
        self.limits = settings['range']
        self.scaler = Scaler(self.state, self.limits)
        self.trigger = None
        if 'trigger' in settings['process']:
            self.trigger = getattr(self.hub, settings['process']['trigger'])

        self.hub.samplers[len(self.hub.samplers)] = self

        self.experiment = getattr(self.hub, settings['experiment']['name'])
        self.experiment_params = settings['experiment']['params']

        self.algorithm = None
        self.algorithm_params = None
        if 'sampler' in settings:
            self.algorithm = recommender.get_class('sampler', settings['sampler']['name'])
            self.algorithm.end_at = settings['process']['end at']
            self.algorithm.sampler = self
            self.algorithm_params = settings['sampler']['params']
            self.algorithm.set_params(self.algorithm_params)
        if 'servo' in settings:
            self.algorithm = recommender.get_class('servo', settings['servo']['name'])
            self.algorithm.sampler = self
            self.algorithm_params = settings['servo']['params']
            self.algorithm.set_params(self.algorithm_params)
        self.skip_lock_check = False           # if True, experiments will disregard watchdog state

        self.model = None
        if 'model' in settings:
            self.model_params = settings['model']['params']
            self.model = recommender.get_class('model', settings['model']['name'])
            if 'Weights' in settings['model']['params']:
                filename = self.hub.core.path['data'] + '/' + settings['model']['params']['Weights'].split('.')[0]
                self.model._import(filename)

        self.active = True        # a boolean allowing early termination through the callback method
        self.start_time = t
        self.hub.macro_buffer.add(self.hub.state)   # save initial state to buffer
        self.prepare(self.state)
        if self.model is not None:
            self.model.prepare(self)


    def __getstate__(self):
        d = {}
        d['experiment_name'] = self.experiment.__name__
        for x in ['limits', 'model', 'algorithm_params', 'experiment_params', 'history', 'state', 'name', 'knobs', 'start_time', 'hub', 'experiment', 'algorithm']:
            d[x] = self.__dict__[x]

        return d

    @thread
    def _run(self):
        count = 0
        while self.active:
            if self.trigger is not None:
                self.trigger()
            result = self._cost({}, norm=False)
            count += 1
            if type(self.experiment_params['iterations']) is int:
                if count >= self.experiment_params['iterations']:
                    break
        self.save(self.start_time.replace(':','') + ' - ' + self.experiment.__name__)
        self.active = False

    @thread
    def _solve(self):
        ''' Runs an algorithm. '''
        self.hub.enable_watchdogs(False)
        points, costs = self.algorithm.run(self.state)
        self.hub.enable_watchdogs(True)
        log.info('Optimization complete!')
        self.save(self.start_time.replace(':','') + ' - ' + self.experiment.__name__ + ' - ' + self.algorithm.name)
        self.active = False

        return points, costs

    def callback(self, *args):
        ''' Check if the sampler is active. This is used to terminate processes
            early by setting the active flag to False, through the GUI or otherwise. '''
        return self.active

    def terminate(self):
        ''' Set a flag to terminate a process early through the callback check. '''
        self.active = False

    def get_history(self):
        ''' Return a multidimensional array and corresponding points from the history df'''
        arrays = []
        state = {}
        costs = self.history['cost'].values
        errors = None
        if 'error' in self.history.columns:
            errors = self.history['error'].values
            if np.isnan(errors).any():
                errors = None
        t = self.history.index.values
        for col in self.history.columns:
            if col not in ['cost', 'error']:
                arrays.append(self.history[col].values)
                thing = col.split(':')[0]
                knob = col.split(':')[1]
                if thing not in state.keys():
                    state[thing] = {}
                state[thing][knob] = 0
        if len(arrays) > 0:
            points = np.vstack(arrays).T.astype(float)
        else:
            points = None
        costs = costs.astype(float)

        return t, points, costs, errors

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

        ''' Update history '''
        t = time.time()
        self.history.loc[t, 'cost'] = c
        self.history.loc[t, 'error'] = error
        for thing in target:
            for knob in target[thing]:
                self.history.loc[t, thing+':'+knob] = norm_target[thing][knob]
        return c

    def get_limits(self):
        ''' Get the limits of all knobs in self.history from the Hub. '''
        limits = {}
        for col in self.history.columns:
            if col in ['cost', 'error']:
                continue
            thing = col.split(':')[0]
            knob = col.split(':')[1]
            limits[col] = self.limits[thing][knob]

        return limits

    def prepare(self, state):
        num_items = 0
        cols = []
        self.knobs = {}
        for thing in state:
            self.knobs[thing] = []
            for knob in state[thing]:
                cols.append(thing+':'+knob)
                num_items += 1
                self.knobs[thing].append(knob)
        state = self.scaler.normalize(state)
        cols.append('cost')
        self.history = pd.DataFrame(columns=cols)
        bounds = np.array(list(itertools.repeat([0, 1], num_items)))
        state = self.scaler.state2array(state)

        self.points = np.atleast_2d([state])
        self.costs = np.array([self._cost(state)])

        # ''' Sample initial point '''
        # c = self._cost(state)
        # if hasattr(self, 'model'):
        #     self.model.append(state, c)

        return self.points, self.costs

    def save(self, filename):
        ''' Byte-serialize the sampler and all attached picklable objects and
            save to file. '''
        self.history.to_csv(self.hub.core.path['data']+filename+'.csv')
        self.hub.macro_buffer.add(self.hub.state)
        try:
            with open(self.hub.core.path['data']+'%s.sci'%filename, 'wb') as file:
                pickle.dump(self, file)
        except Exception as e:
            log.warning('Could not pickle Sampler state:', e)
