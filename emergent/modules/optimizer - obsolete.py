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
from scipy.optimize import curve_fit, minimize, differential_evolution, basinhopping
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-2]))
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, WhiteKernel
from sklearn.decomposition import PCA, IncrementalPCA, KernelPCA
from scipy.sparse.csgraph import dijkstra
import sklearn.cluster
from emergent.modules.visualization import plot_1D, plot_2D
# from algorithms.neural_network import NeuralNetwork
from sklearn import metrics
import pandas as pd
import time
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn
from emergent.utility import methodsWithDecorator, algorithm, servo
from emergent.modules import Sampler

class Optimizer():
    ''' General methods '''
    def __init__(self, hub_node, cost = None):
        ''' Initialize the optimizer and link to the parent Hub. '''
        self.parent = hub_node

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



    ''' Hyperparameter optimization '''
    def tune(self):
        state = {'thingA': {'X': 0, 'Y': 0}}
        cost_params = {"x0": 0.3,
                       "noise": 0.01,
                       "y0": 0.6,
                       "sigma_y": 0.8,
                       "theta": 0,
                       "sigma_x": 0.3,
                       "cycles per sample": 1}
        cost = self.sampler.hub.cost_uncoupled
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
