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
from emergent.utilities.plotting import plot_1D

class Sampler():
    ''' General methods '''
    def __init__(self, name, settings, t=None):

        ''' Initialize the sampler and link to the parent Hub. '''
        self.name = name
        if t is None:
            t = datetime.datetime.now().strftime('%Y%m%dT%H%M')
        self.state = settings['state']
        self.hub = settings['hub']
        self.limits = settings['range']
        self.trigger = None
        self.index = len(self.hub.samplers)
        self.hub.samplers[self.index] = self
        self.experiment = settings['experiment']['instance']
        self.experiment_name = self.experiment.__name__
        self.experiment_params = settings['experiment']['params']

        self.algorithm = None
        self.algorithm_params = None
        if 'sampler' in settings:
            self.algorithm = settings['sampler']['instance']
            self.algorithm.end_at = settings['process']['end at']
            self.algorithm.sampler = self
            self.algorithm_params = settings['sampler']['params']
            self.algorithm.set_params(self.algorithm_params)
        if 'servo' in settings:
            self.algorithm = settings['servo']['instance']
            self.algorithm.sampler = self
            self.algorithm_params = settings['servo']['params']
            self.algorithm.set_params(self.algorithm_params)
        self.skip_lock_check = False           # if True, experiments will disregard watchdog state

        self.model = None
        if 'model' in settings:
            if settings['model']['instance'] is not None:
                self.model_params = settings['model']['params']
                self.model = settings['model']['instance']
                self.model.prepare(self)


        self.actuate = self.hub.actuate
        self.active = True        # a boolean allowing early termination through the callback method
        self.progress = 0
        self.result = None
        self.start_time = t
        self.hub.macro_buffer.add(self.hub.state)   # save initial state to buffer
        self.prepare(self.state)

    def __getstate__(self):
        d = {}
        d['experiment_name'] = self.experiment.__name__
        for x in ['limits', 'model', 'algorithm_params', 'experiment_params', 'history', 'state', 'name', 'knobs', 'start_time', 'hub', 'experiment', 'algorithm']:
            d[x] = self.__dict__[x]

        return d

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
        self.log(self.start_time.replace(':','') + ' - ' + self.experiment.__name__)
        self.active = False

    def _solve(self):
        ''' Runs an algorithm. '''
        self.hub.enable_watchdogs(False)
        points, costs = self.algorithm.run(self.state)
        self.hub.enable_watchdogs(True)
        log.info('Optimization complete!')
        self.log(self.start_time.replace(':','') + ' - ' + self.experiment.__name__ + ' - ' + self.algorithm.name)
        self.active = False

        return points, costs

    def callback(self, *args):
        ''' Check if the sampler is active. This is used to terminate processes
            early by setting the active flag to False, through the GUI or otherwise. '''
        return self.active

    def log(self, filename):
        ''' Saves the sampled data to file and updates the buffer '''
        self.history.to_csv(self.hub.network.path['data']+filename+'.csv')
        self.hub.macro_buffer.add(self.hub.state)
        self.save(filename)

    def terminate(self):
        ''' Set a flag to terminate a process early through the callback check. '''
        self.active = False

    ''' State conversion functions '''
    def array2state(self, arr):
        ''' Converts a numpy array into a state dict with keys matching self.state. '''
        state = {}
        i = 0
        for thing in self.state:
            state[thing] = {}
            for knob in self.state[thing]:
                state[thing][knob] = arr[i]
                i += 1
        return state

    def state2array(self, state):
        ''' Converts a state dict into a numpy array. '''
        arr = np.array([])
        for thing in state:
            for knob in state[thing]:
                arr = np.append(arr, state[thing][knob])
        return arr

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
                thing = col.split('.')[0]
                knob = col.split('.')[1]
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
            norm_target = self.array2state(state)
        else:
            norm_target = state
        if norm:
            target = self.unnormalize(norm_target)
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
        self.result = c
        for thing in target:
            for knob in target[thing]:
                self.history.loc[t, thing+'.'+knob] = norm_target[thing][knob]
        return c

    def estimate_gradient(self, arr, step_size):
        gradient = np.array([])
        for i in range(len(arr)):
            step = np.zeros(len(arr))
            step[i] = step_size
            g_i = (self._cost(arr+step/2)-self._cost(arr-step/2))/step_size
            gradient = np.append(gradient, g_i)
        return gradient

    def get_limits(self):
        ''' Get the limits of all knobs in self.history from the Hub. '''
        limits = {}
        for col in self.history.columns:
            if col in ['cost', 'error']:
                continue
            thing = col.split('.')[0]
            knob = col.split('.')[1]
            limits[col.replace('.', ': ')] = self.limits[thing][knob]

        return limits

    def prepare(self, state):
        num_items = 0
        cols = []
        self.knobs = {}
        for thing in state:
            self.knobs[thing] = []
            for knob in state[thing]:
                cols.append(thing+'.'+knob)
                num_items += 1
                self.knobs[thing].append(knob)
        state = self.normalize(state)
        cols.append('cost')
        self.history = pd.DataFrame(columns=cols)
        bounds = np.array(list(itertools.repeat([0, 1], num_items)))
        state = self.state2array(state)

        # ''' Sample initial point '''
        # c = self._cost(state)
        # if hasattr(self, 'model'):
        #     self.model.append(state, c)

        return state, bounds

    def normalize(self, unnorm):
        ''' Normalizes a state or substate based on min/max values of the Knobs,
            saved in the parent Hub. '''
        norm = {}

        for thing in unnorm:
            norm[thing] = {}
            for i in unnorm[thing]:
                min_val = self.limits[thing][i]['min']
                max_val = self.limits[thing][i]['max']
                norm[thing][i] = (unnorm[thing][i] - min_val)/(max_val-min_val)

        return norm

    def unnormalize(self, norm, return_array=False):
        ''' Converts normalized (0-1) state to physical state based on specified
            max and min parameter values. '''
        if isinstance(norm, np.ndarray):
            norm = self.array2state(norm)
        unnorm = {}
        for thing in norm:
            unnorm[thing] = {}
            for i in norm[thing]:
                min_val = self.limits[thing][i]['min']
                max_val = self.limits[thing][i]['max']
                unnorm[thing][i] = min_val + norm[thing][i] * (max_val-min_val)
        if return_array:
            return self.state2array(unnorm)
        return unnorm

    def save(self, filename):
        ''' Byte-serialize the sampler and all attached picklable objects and
            save to file. '''
        try:
            with open(self.hub.network.path['data']+'%s.sci'%filename, 'wb') as file:
                pickle.dump(self, file)
        except Exception as e:
            log.warning('Could not pickle Sampler state:', e)

    ''' Visualization methods '''
    def plot_optimization(self):
        ''' Plots an optimization time series stored in self.history. '''
        t, points, costs, errors = self.get_history()
        t = t.copy() - t[0]
        ax, fig = plot_1D(t,
                          -costs,
                          errors=errors,
                          xlabel='Time (s)',
                          ylabel=self.experiment.__name__)

        return fig

    ''' Sampling methods '''
    def sample(self, state, method='random_sampling', points=1, bounds=None):
        ''' Returns a list of points sampled with the specified method, as well as
            the cost function evaluated at these points. '''
        if bounds is None:
            bounds = np.array(list(itertools.repeat([0, 1], len(state.keys()))))
        func = getattr(self, method)
        points, cost = func(state, int(points), bounds)

        return points, cost

    # def random_sampling(self,state, points, bounds, callback = None):
    #     ''' Performs a random sampling of the cost function at N points within
    #         the specified bounds. '''
    #     if callback is None:
    #         callback = self.callback
    #     dof = sum(len(state[x]) for x in state)
    #     points = np.random.uniform(size=(int(points),dof))
    #     costs = []
    #     for point in points:
    #         if not callback():
    #             return points[0:len(costs)], costs
    #         c = self._cost(point)
    #         costs.append(c)
    #
    #     return points, costs
