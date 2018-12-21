''' This script implements an Aligner class from which many things inherit methods such as:
    persistent positioning, first light acquisition, and realtime optimization
'''
''' TODO: store position indices for each thing, actuate functions should be threaded,
    pca/dimensionality reduction/covariance/clustering, image convolution, drift record analysis
'''
import threading
import logging as log
import numpy as np
import itertools
import sys
import os
from scipy.interpolate import griddata
from scipy.stats import norm
import matplotlib.pyplot as plt
import pickle
from emergent.modules.visualization import plot_1D, plot_2D
import pandas as pd
import time
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn
from emergent.utility import methodsWithDecorator, algorithm

class Sampler():
    ''' General methods '''
    def __init__(self, name, state, hub, experiment, experiment_params, algorithm = None, algorithm_params = {}, t = None):
        ''' Initialize the sampler and link to the parent Hub. '''
        self.name = name
        self.state = state
        self.hub = hub
        self.index = len(hub.samplers)
        hub.samplers[self.index] = self
        self.experiment = experiment
        self.experiment_name = experiment.__name__
        self.experiment_params = experiment_params
        self.algorithm = algorithm
        if self.algorithm is not None:
            self.algorithm.sampler = self
        self.algorithm_params = algorithm_params

        self.actuate = self.hub.actuate
        self.active = True        # a boolean allowing early termination through the callback method
        self.progress = 0
        self.result = None
        self.start_time = t
        self.hub.macro_buffer.add(self.hub.state)   # save initial state to buffer
        self.priority = False           # if True, experiments will disregard watchdog state
        self.prepare(self.state)

    def __getstate__(self):
        d = {}
        d['experiment_name'] = self.experiment.__name__
        for x in ['algorithm_params', 'experiment_params', 'history', 'state', 'name', 'inputs', 'start_time', 'hub', 'experiment', 'algorithm']:
            d[x] = self.__dict__[x]

        return d

    def callback(self, *args):
        return self.active

    def log(self, filename):
        ''' Saves the sampled data to file and updates the buffer '''
        self.history.to_csv(self.hub.network.data_path+filename+'.csv')
        self.hub.macro_buffer.add(self.hub.state)
        self.hub.process_signal.emit(self.hub.state)
        self.save(filename)

    def terminate(self):
        self.active = False

    ''' State conversion functions '''
    def array2state(self, arr):
        ''' Converts a numpy array into a state dict with keys matching self.state. '''
        state = {}
        i = 0
        for thing in self.state:
            state[thing] = {}
            for input in self.state[thing]:
                state[thing][input] = arr[i]
                i += 1
        return state

    def state2array(self, state):
        ''' Converts a state dict into a numpy array. '''
        arr = np.array([])
        for thing in state:
            for input in state[thing]:
                arr = np.append(arr, state[thing][input])
        return arr

    def get_history(self, include_database = False):
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
                input = col.split('.')[1]
                if thing not in state.keys():
                    state[thing] = {}
                state[thing][input] = 0
        points = np.vstack(arrays).T.astype(float)
        costs = costs.astype(float)

        if include_database:
            points, costs = self.search_database(points, costs, state, self.experiment)
        return t, points, costs, errors

    def search_database(self, points, costs, state, cost):
        ''' Prepare a state dict of all variables which are held constant during optimization '''
        constant_state = self.hub.state.copy()
        for thing in state.keys():
            for input in state[thing]:
                del constant_state[thing][input]

        ''' Search the database for entries matching these constant values '''
        database = self.hub.dataframe['cost'][cost.__name__]
        subdf = database
        for thing in constant_state.keys():
            for input in constant_state[thing]:
                subdf = subdf[np.isclose(subdf[thing+': '+input],constant_state[thing][input], atol = 1e-12)]

        ''' Form points, costs arrays '''
        for i in range(len(subdf)):
            old_state = {}
            for thing in state.keys():
                old_state[thing] = {}
                for input in state[thing]:
                    old_state[thing][input] = subdf.iloc[i][thing+': '+input]
                    points = np.append(points, np.atleast_2d(self.state2array(self.normalize(old_state))), axis=0)
                    costs = np.append(costs, subdf.iloc[i][cost.__name__])
        return points, costs

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
        c, error = self.experiment(self, target)

        ''' Update history '''
        t = time.time()
        self.history.loc[t,'cost']=c
        self.history.loc[t,'error'] = error
        self.result = c
        for thing in target:
            for input in target[thing]:
                self.history.loc[t,thing+'.'+input] = norm_target[thing][input]
        return c

    def estimate_gradient(self, arr, step_size):
        g = np.array([])
        for i in range(len(arr)):
            step = np.zeros(len(arr))
            step[i] = step_size
            gi = (self._cost(arr+step/2)-self._cost(arr-step/2))/step_size
            g = np.append(g, gi)
        return g

    def get_limits(self):
        limits = {}
        for col in self.history.columns:
            if col in ['cost', 'error']:
                continue
            thing = col.split('.')[0]
            input = col.split('.')[1]
            limits[col.replace('.', ': ')] =  self.hub.settings[thing][input]

        return limits

    def prepare(self, state):
        num_items = 0
        cols = []
        self.inputs = {}
        for thing in state:
            self.inputs[thing] = []
            for input in state[thing]:
                cols.append(thing+'.'+input)
                num_items += 1
                self.inputs[thing].append(input)
        state = self.normalize(state)
        cols.append('cost')
        self.history = pd.DataFrame(columns=cols)
        bounds = np.array(list(itertools.repeat([0,1], num_items)))
        state = self.state2array(state)

        return state, bounds

    def normalize(self, unnorm):
        ''' Normalizes a state or substate based on min/max values of the Inputs,
            saved in the parent Hub. '''
        norm = {}

        for thing in unnorm:
            norm[thing] = {}
            for i in unnorm[thing]:
                min = self.hub.settings[thing][i]['min']
                max = self.hub.settings[thing][i]['max']
                norm[thing][i] = (unnorm[thing][i] - min)/(max-min)

        return norm

    def unnormalize(self, norm, return_array = False):
        ''' Converts normalized (0-1) state to physical state based on specified
            max and min parameter values. '''
        if type(norm) == np.ndarray:
            norm = self.array2state(norm)
        unnorm = {}
        for thing in norm:
            unnorm[thing] = {}
            for i in norm[thing]:
                min = self.hub.settings[thing][i]['min']
                max = self.hub.settings[thing][i]['max']
                unnorm[thing][i] = min + norm[thing][i] * (max-min)
        if return_array:
            return self.state2array(unnorm)
        else:
            return unnorm

    def save(self, filename):
        with open(self.hub.network.data_path+'%s.sci'%filename, 'wb') as file:
            pickle.dump(self, file)

    ''' Visualization methods '''
    def plot_optimization(self, yscale = 'linear'):
        ''' Plots an optimization time series stored in self.history. '''
        t, points, costs, errors = self.get_history()
        t = t.copy() - t[0]
        ax, fig = plot_1D(t, -costs, errors=errors, xlabel='Time (s)', ylabel = self.experiment.__name__)

        return fig

    ''' Sampling methods '''
    def sample(self, state, method='random_sampling', points = 1, bounds = None):
        ''' Returns a list of points sampled with the specified method, as well as
            the cost function evaluated at these points. '''
        if bounds is None:
            bounds = np.array(list(itertools.repeat([0,1], len(state.keys()))))
        func = getattr(self, method)
        points, cost = func(state, int(points), bounds)

        return points, cost

    def random_sampling(self,state, points, bounds, callback = None):
        ''' Performs a random sampling of the cost function at N points within
            the specified bounds. '''
        if callback is None:
            callback = self.callback
        dof = sum(len(state[x]) for x in state)
        points = np.random.uniform(size=(int(points),dof))
        costs = []
        for point in points:
            if not callback():
                return points[0:len(costs)], costs
            c = self._cost(point)
            costs.append(c)

        return points, costs

    def grid_sampling(self, state, points, args=None, norm = True, callback = None):
        ''' Performs a uniformly-spaced sampling of the cost function in the
            space spanned by the passed-in state dict. '''
        if callback is None:
            callback = self.callback
        arr, bounds = self.prepare(state)
        N = len(arr)
        grid = []
        for n in range(N):
            space = np.linspace(bounds[n][0], bounds[n][1], int(points))
            grid.append(space)
        grid = np.array(grid)
        points = np.transpose(np.meshgrid(*[grid[n] for n in range(N)])).reshape(-1,N)

        ''' Actuate search '''
        costs = np.array([])
        for point in points:
            if not callback():
                return points[0:len(costs)], costs
            c = self._cost(point)

            costs = np.append(costs, c)
            self.progress = len(costs) / len(points)

        return points, costs
