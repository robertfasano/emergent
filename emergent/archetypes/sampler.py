''' This script implements an Aligner class from which many devices inherit methods such as:
    persistent positioning, first light acquisition, and realtime optimization
'''
''' TODO: store position indices for each device, actuate functions should be threaded,
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

from emergent.archetypes.visualization import plot_1D, plot_2D
# from algorithms.neural_network import NeuralNetwork
import pandas as pd
import time
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn
from emergent.utility import methodsWithDecorator, algorithm
from copy import deepcopy

class Sampler():
    ''' General methods '''
    def __init__(self, control_node, cost = None):
        ''' Initialize the sampler and link to the parent Control node. '''
        self.parent = control_node
        self.actuate = self.parent.actuate
        self.active = True        # a boolean allowing early termination through the callback method
        self.progress = 0
        self.result = None
        self.cost = cost

    def callback(self, *args):
        return self.active

    def log(self, filename):
        ''' Saves the sampled data to file with the given name '''
        self.history.to_csv(self.parent.data_path+filename+'.csv')

    def terminate(self):
        self.active = False
        if hasattr(self, 'optimizer'):
            self.optimizer.active = False

    ''' State conversion functions '''
    def array2state(self, arr, d):
        ''' Converts a numpy array into a state dict with the specified keys. '''
        state = {}
        i = 0
        for dev in d:
            state[dev] = {}
            for input in d[dev]:
                state[dev][input] = arr[i]
                i += 1
        return state

    def cost_from_array(self, arr, d, cost, cost_params):
        ''' Converts the array back to the form of d,
            unnormalizes it, and returns cost evaluated on the result. '''
        norm_target = self.array2state(arr, d)
        target = self.unnormalize(norm_target)

        c = cost(target, cost_params)
        ''' Update history '''
        t = time.time()
        self.history.loc[t,'cost']=c
        self.result = c
        for dev in d:
            for input in d[dev]:
                self.history.loc[t,dev+'.'+input] = norm_target[dev][input]
        return c

    def get_history(self, include_database = False):
        ''' Return a multidimensional array and corresponding points from the history df'''
        arrays = []
        state = {}
        costs = self.history['cost'].values
        t = self.history.index.values
        for col in self.history.columns:
            if col != 'cost':
                arrays.append(self.history[col].values)
                dev = col.split('.')[0]
                input = col.split('.')[1]
                if dev not in state.keys():
                    state[dev] = {}
                state[dev][input] = 0
        points = np.vstack(arrays).T.astype(float)
        costs = costs.astype(float)

        if include_database:
            points, costs = self.search_database(points, costs, state, self.cost)
        return t, points, costs

    def search_database(self, points, costs, state, cost):
        ''' Prepare a state dict of all variables which are held constant during optimization '''
        constant_state = deepcopy(self.parent.state)
        for dev in state.keys():
            for input in state[dev]:
                del constant_state[dev][input]

        ''' Search the database for entries matching these constant values '''
        database = self.parent.dataframe['cost'][cost.__name__]
        subdf = database
        for dev in constant_state.keys():
            for input in constant_state[dev]:
                subdf = subdf[np.isclose(subdf[dev+': '+input],constant_state[dev][input], atol = 1e-12)]

        ''' Form points, costs arrays '''
        for i in range(len(subdf)):
            old_state = {}
            for dev in state.keys():
                old_state[dev] = {}
                for input in state[dev]:
                    old_state[dev][input] = subdf.iloc[i][dev+': '+input]
                    points = np.append(points, np.atleast_2d(self.state2array(self.normalize(old_state))), axis=0)
                    costs = np.append(costs, subdf.iloc[i][cost.__name__])
        return points, costs

    def state2array(self, state):
        ''' Converts a state dict into a numpy array. '''
        arr = np.array([])
        for dev in state:
            for input in state[dev]:
                arr = np.append(arr, state[dev][input])
        return arr

    ''' Logistics functions '''
    def _cost(self, state, params = {}):
        ''' Computes the cost and logs. '''
        c = self.cost(state, params)
        t = time.time()
        self.history.loc[time.time()] = c
        for dev in state:
            for input in state[dev]:
                self.history.loc[t,dev+'.'+input] = state[dev][input]
        return c

    def initialize(self, state, cost, params, cost_params):
        ''' Creates a history dataframe to log the sampling. Normalizes the
            state in terms of the min/max of each Input node, then prepares a
            bounds array. '''
        self.cost = cost
        self.cost_name = cost.__name__
        self.params = params
        self.cost_params = cost_params
        self.inputs = {}
        num_items = 0
        cols = []
        for dev in state:
            self.inputs[dev] = []
            for input in state[dev]:
                cols.append(dev+'.'+input)
                num_items += 1
                self.inputs[dev].append(input)
        state = self.normalize(state)
        cols.append('cost')
        self.history = pd.DataFrame(columns=cols)
        bounds = np.array(list(itertools.repeat([0,1], num_items)))
        state = self.state2array(state)
        return state, bounds

    def normalize(self, unnorm):
        ''' Normalizes a state or substate based on min/max values of the Inputs,
            saved in the parent Control node. '''
        norm = {}

        for dev in unnorm:
            norm[dev] = {}
            for i in unnorm[dev]:
                min = self.parent.settings[dev][i]['min']
                max = self.parent.settings[dev][i]['max']
                norm[dev][i] = (unnorm[dev][i] - min)/(max-min)

        return norm

    def unnormalize(self, norm):
        ''' Converts normalized (0-1) state to physical state based on specified
            max and min parameter values. '''
        unnorm = {}
        for dev in norm:
            unnorm[dev] = {}
            for i in norm[dev]:
                min = self.parent.settings[dev][i]['min']
                max = self.parent.settings[dev][i]['max']
                unnorm[dev][i] = min + norm[dev][i] * (max-min)
        return unnorm

    ''' Visualization methods '''
    def plot_optimization(self, yscale = 'linear'):
        ''' Plots an optimization time series stored in self.history. '''
        func = self.history.copy()
        func.index -= func.index[0]
        plt.figure()
        plt.plot(func['cost'])
        plt.yscale(yscale)
        plt.ylabel(self.cost.__name__)
        plt.xlabel('Time (s)')
        plt.show()

    def plot_history_slice(self, i):
        ''' Plots a slice of the ith element of the history. '''
        df = self.history.iloc[i]
        del df['cost']
        df.plot()
        plt.ylim([-5,8])
        plt.xlabel('Time')
        plt.ylabel('Setpoint')
        plt.savefig(self.parent.data_path + 'history%i.png'%i)
        plt.close()
