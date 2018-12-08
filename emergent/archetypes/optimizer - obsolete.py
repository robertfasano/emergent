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
from scipy.optimize import curve_fit, minimize, differential_evolution, basinhopping
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-2]))
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, WhiteKernel
from sklearn.decomposition import PCA, IncrementalPCA, KernelPCA
from scipy.sparse.csgraph import dijkstra
import sklearn.cluster
from emergent.archetypes.visualization import plot_1D, plot_2D
# from algorithms.neural_network import NeuralNetwork
from sklearn import metrics
import pandas as pd
import time
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn
from emergent.utility import methodsWithDecorator, algorithm, servo
from emergent.archetypes import Sampler

class Optimizer():
    ''' General methods '''
    def __init__(self, control_node, cost = None):
        ''' Initialize the optimizer and link to the parent Control node. '''
        self.parent = control_node
        self.actuate = self.parent.actuate
        self.active = True        # a boolean allowing early termination through the callback method
        self.progress = 0
        self.result = None
        self.cost = cost
        self.sampler = Sampler(control_node, cost = cost)

    def callback(self, *args):
        return self.active

    def log(self, filename):
        ''' Saves the results of the optimization to file with the given name '''
        self.sampler.history.to_csv(self.parent.data_path+filename+'.csv')

    def terminate(self):
        self.active = False

    def dijkstra_sampling(self, points, weights = None):
        ''' Determines the sampling order of the given points array to minimize
            the distance between points, weighted by an optional vector. The
            weight vector allows consideration of different actuation speeds
            in the path decision. NOTE: not yet tested. '''
        if weights is None:
            weights = np.ones(len(points))

        ''' First, calculate an adjacency matrix G, where G[i,j] is the distance
            between points[i] and points[j] '''
        G = np.zeros((len(points), len(points)))
        for i in range(len(points)):
             for j in range(len(points)):
                 G[i,j] = np.linalg.norm(weights*points[i]-weights*points[j])

        dist_matrix = dijkstra(G)

    ''' Optimization routines '''


    ''' Hyperparameter optimization '''
    def tune(self):
        state = {'deviceA': {'X': 0, 'Y': 0}}
        cost_params = {"x0": 0.3,
                       "noise": 0.01,
                       "y0": 0.6,
                       "sigma_y": 0.8,
                       "theta": 0,
                       "sigma_x": 0.3,
                       "cycles per sample": 1}
        cost = self.sampler.parent.cost_uncoupled
        algorithm = self.adam
        params={'learning rate':0.1, 'steps': 100, 'dither': 0.01, 'beta_1': 0.9, 'beta_2': 0.999, 'epsilon': 1e-8}
        pmin = 0.001
        pmax = 0.1
        steps = 10
        loss = []
        for p in np.logspace(pmin, pmax, steps):
            params['dither'] = p
            algorithm(state, cost, params, cost_params)
            loss.append(self.sampler.history['cost'].iloc[-1])
            print(loss)
        return loss

    ''' Control methods '''
    @servo
    def PID(self, state, error, params={'proportional_gain':1, 'integral_gain':0, 'derivative_gain':0, 'sign':1}, error_params = {}, callback = None):
        self.sampler.initialize(state, error, params, error_params)
        if callback is None:
            callback = self.callback
        devices = list(state.keys())
        assert len(devices) == 1
        dev = devices[0]

        inputs = list(state[dev].keys())
        assert len(inputs) == 1
        input = inputs[0]
        input_node = self.parent.children[dev].children[input]
        input_node.error_history = pd.Series()
        last_error = error(state, error_params)
        last_time = time.time()
        integral = 0
        e = None
        while callback(e):
            e = error(state, error_params)
            t = time.time()
            print(t)
            self.sampler.history.loc[t,'cost']=e
            for dev in state:
                for input in state[dev]:
                    self.sampler.history.loc[t,dev+'.'+input] = state[dev][input]
            print('State:', state, 'Error:', e)
            delta_t = t - last_time
            delta_e = e - last_error

            proportional = params['proportional_gain'] * e
            integral += params['integral_gain'] * e * delta_t
            derivative = params['derivative_gain'] * delta_e/delta_t

            last_time = t
            last_error = e

            target = proportional + integral + derivative
            state[dev][input] -= params['sign']*target  # gets passed into error in the next loop

    ''' Visualization methods '''
    def plot_optimization(self, yscale = 'linear'):
        ''' Plots an optimization time series stored in self.sampler.history. '''
        func = self.sampler.history.copy()
        func.index -= func.index[0]
        fig = plt.figure()
        plt.plot(func['cost'])
        plt.yscale(yscale)
        plt.ylabel(self.cost.__name__)
        plt.xlabel('Time (s)')
        return fig

    def plot_history_slice(self, i):
        ''' Plots a slice of the ith element of the history. '''
        df = self.sampler.history.iloc[i]
        del df['cost']
        df.plot()
        plt.ylim([-5,8])
        plt.xlabel('Time')
        plt.ylabel('Setpoint')
        plt.savefig(self.parent.data_path + 'history%i.png'%i)
        plt.close()
