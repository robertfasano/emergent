''' This script implements an Aligner class from which many devices inherit methods such as:
    persistent positioning, first light acquisition, and realtime optimization
'''
''' TODO: store position indices for each device, actuate functions should be threaded,
    pca/dimensionality reduction/covariance/clustering, image convolution, drift record analysis
'''
import numpy as np
import itertools
import sys
import os
from scipy.interpolate import griddata
from scipy.stats import norm
import matplotlib.pyplot as plt
plt.ion()
from scipy.optimize import curve_fit, minimize, differential_evolution, basinhopping
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-2]))
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, WhiteKernel
from sklearn.decomposition import PCA, IncrementalPCA, KernelPCA
from scipy.sparse.csgraph import dijkstra
import sklearn.cluster
from sklearn import metrics
import pandas as pd
import time
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn
from utility import methodsWithDecorator, algorithm 

class Optimizer():
    ''' General methods '''
    def __init__(self, control_node):
        ''' Initialize the optimizer and link to the parent Control node. '''
        self.parent = control_node
        self.actuate = self.parent.actuate

    def array2dict(self, arr, keys):
        ''' Converts a numpy array into a state dict with the specified keys. '''
        state = {}
        for i in range(len(keys)):
            state[keys[i]] = arr[i]
        return state

    def dict2array(self, state):
        ''' Converts a state dict into a numpy array. '''
        arr = np.array([])
        for i in range(len(state.keys())):
            arr = np.append(arr, state[list(state.keys())[i]])
        return arr

    def _cost(self, state, cost):
        ''' Unnormalizes the state dict, computes the cost, and logs. '''
        c = cost(self.unnormalize(state))
        self.history.loc[time.time()] = -c
        return c

    def cost_array(self, X, keys, cost):
        ''' Converts a normalized array into a state dict and evaluates cost. '''
        state = self.array2dict(X, keys)
        return self._cost(state, cost)

    def initialize_optimizer(self, state):
        ''' Creates a history dataframe to log the optimization. Normalizes the
            state in terms of the min/max of each Input node, then prepares a
            bounds array. '''
        cols = list(state.keys())
        cols.append('cost')
        self.history = pd.DataFrame(index = [], columns = cols)
        state = self.normalize(state)
        bounds = np.array(list(itertools.repeat([0,1], len(state.keys()))))

        return state, bounds

    def list_algorithms(self):
        ''' Returns a list of all methods tagged with the '@algorithm' decorator '''
        return methodsWithDecorator(Optimizer, 'algorithm')

    def normalize(self, unnorm):
        ''' Normalizes a state or substate based on min/max values of the Inputs,
            saved in the parent Control node. '''
        norm = {}
        for i in unnorm.keys():
            min = self.parent.settings[i]['min']
            max = self.parent.settings[i]['max']
            norm[i] = (unnorm[i] - min)/(max-min)
        return norm

    def unnormalize(self, norm):
        ''' Converts normalized (0-1) state to physical state based on specified
            max and min parameter values. '''
        unnorm = {}

        for i in norm.keys():
                min = self.parent.settings[i]['min']
                max = self.parent.settings[i]['max']
                unnorm[i] = min + norm[i] * (max-min)
        return unnorm

    ''' Sampling methods '''
    def sample(self, state, cost, method='random_sampling', points = 1, bounds = None):
        ''' Returns a list of points sampled with the specified method, as well as
            the cost function evaluated at these points. '''
        if bounds is None:
            bounds = np.array(list(itertools.repeat([0,1], len(state.keys()))))
        func = getattr(self, method)
        points, cost = func(state, cost, points, bounds)

        return points, cost

    def grid_sampling(self, state, cost, points, bounds, update=None, args=None, norm = True):
        ''' Performs a uniformly-spaced sampling of the cost function in the
            space spanned by the passed-in state dict. '''
        N = len(state.keys())
        grid = []
        for n in range(N):
            space = np.linspace(bounds[n][0], bounds[n][1], points)
            grid.append(space)
        grid = np.array(grid)
        points = np.transpose(np.meshgrid(*[grid[n] for n in range(N)])).reshape(-1,N)

        ''' Actuate search '''
        costs = []
        for point in points:
            target = self.array2dict(point, list(state.keys()))
            if norm:
                target = self.unnormalize(target)
            if args is None:
                costs.append(cost(target))
            else:
                costs.append(cost(target,args))
            if update is not None:
                update(len(costs)/len(points))
                # print(len(costs)/len(points))

        points = np.array(points)
        costs = np.array(costs)
        np.savetxt('costs.txt', costs)
        np.savetxt('points.txt', points)

        return points, costs

    def random_sampling(self,state, cost, points, bounds):
        ''' Performs a random sampling of the cost function at N points within
            the specified bounds. '''
        points = np.random.uniform(size=(points,len(state.keys())))
        print(points)
        print(points.shape)
        costs = []
        for point in points:
            target = self.array2dict(point, list(state.keys()))
            costs.append(cost(self.unnormalize(target)))

        return points, costs

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
    def optimize(self, state, cost, method, params = None, plot = True):
        ''' Runs a targeted optimization routine on the cost function in the
            space spanned by the state dict. '''
        func = getattr(self, method)
        points, cost = func(state, cost, params)

    @algorithm
    def grid_search(self, state, cost, params={'plot':0, 'loadExisting':0, 'steps':10}, update=None):
        ''' An N-dimensional grid search (brute force) optimizer. '''
        state, bounds = self.initialize_optimizer(state)
        if params['loadExisting']:
            costs = np.loadtxt('costs.txt')
            points = np.loadtxt('points.txt')
        else:
            ''' Generate search grid '''
            points, costs = self.grid_sampling(state, cost, params['steps'], bounds, update=update)

        ''' Plot result if desired '''
        ax = None
        if params['plot'] and len(state.keys()) is 2:
            ax = self.plot_2D(points, costs)
        best_point = self.array2dict(points[np.argmin(costs)], list(state.keys()))
        self.actuate(self.unnormalize(best_point))

        return points, costs

    def gp_next_sample(self, X, bounds, b, cost, gaussian_process, restarts=25):
        ''' Generates the next sampling point by minimizing cost on the virtual
            response surface modeled by the Gaussian process. '''
        best_x = None
        best_acquisition_value = 999

        for starting_point in np.random.uniform(bounds[0][0], bounds[0][1], size=(restarts, X.shape[1])):
            res = minimize(fun=cost,
                       x0=starting_point.reshape(1, -1),
                       bounds=bounds,
                       method='L-BFGS-B',
                       args=(b, gaussian_process))
            if res.fun < best_acquisition_value:
                best_acquisition_value = res.fun
                best_x = res.x

        return best_x

    def gp_effective_cost(self, x, b, gp):
        ''' Computes an effective cost for Gaussian process optimization, featuring
            some tradeoff between optimization and learning. '''
        ''' Watch for function recieveing a 2d x with higher dimensional state vectors (disagreement with internal GP dimension) '''
        mu, sigma = gp.predict(np.atleast_2d(x), return_std = True)
       # return (b*mu+np.sqrt(1-b**2)*sigma)
        return b*mu-(1-b)*sigma

    @algorithm
    def gaussian_process(self, state, cost, params={'batch_size':10,'presampled': 15, 'iterations':10, 'plot':0},update=None):
        ''' Online Gaussian process regression. Batch sampling is done with
            points with varying trade-off of optimization vs. exploration. '''
        state, bounds = self.initialize_optimizer(state)
        X = self.dict2array(state)
        c = np.array([self._cost(state,cost)])

        points, costs = self.sample(state, cost, 'random_sampling', params['presampled'])
        X = np.append(np.atleast_2d(X), points, axis=0)
        c = np.append(c, costs)
        kernel = C(1.0, (1e-3, 1e3)) * RBF(10, (1e-2, 1e2))
        self.gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10)
        for i in range(params['iterations']):
            self.gp.fit(X,c)
            for j in range(params['batch_size']):
                b = j / (params['batch_size']-1)
                X_new = self.gp_next_sample(X, bounds, b, self.gp_effective_cost, self.gp, restarts=10)
                X_new = np.atleast_2d(X_new)
                X = np.append(X, X_new, axis=0)
                target = self.array2dict(X[-1], list(state.keys()))
                c = np.append(c, self._cost(target, cost))
                if update is not None:
                    update((j+i*params['batch_size'])/params['batch_size']/params['iterations'])
        best_point = self.array2dict(X[np.argmin(c)], list(state.keys()))
        print(best_point)
        print(self.unnormalize(best_point))
        self.actuate(self.unnormalize(best_point))
        if params['plot']:
            self.plot_optimization(lbl = 'Gaussian Processing')

        return X, c

    @algorithm
    def scipy_minimize(self, state, cost, params={'method':'L-BFGS-B', 'plot':0, 'tol':1e-7}, update=None):
        ''' Runs a specified scipy minimization method on the target axes and cost. '''
        state, bounds = self.initialize_optimizer(state)
        X = self.dict2array(state)
        keys = list(state.keys())
        res = minimize(fun=self.cost_array,
                   x0=X,
                   bounds=bounds,
                   args = (keys, cost),
                   method=params['method'],
                   tol = params['tol'])
        if params['plot']:
            self.plot_optimization(lbl = params['method'])
        return None, None

    @algorithm
    def simplex(self, state, cost, params={'plot':0, 'tol':1e-7}, update=None):
        ''' Nelder-Mead algorithm from scipy.optimize. '''
        state, bounds = self.initialize_optimizer(state)
        X = self.dict2array(state)
        keys = list(state.keys())
        res = minimize(fun=self.cost_array,
                   x0=X,
                   args = (keys, cost),
                   method='Nelder-Mead',
                   tol = params['tol'])
        #simplex for SKL is res = minimize(fun = cost,x0 = X.reshape(1, -1), method = 'Nelder-Mead', tol = 1e7)
        if params['plot']:
            self.plot_optimization(lbl = 'simplex')
        return None, None

    @algorithm
    def differential_evolution(self, state, cost, params={'strategy':'best1bin', 'plot':0, 'popsize':15, 'tol':0.01, 'mutation': 1,'recombination':0.7}, update=None):
        ''' Differential evolution algorithm from scipy.optimize. '''
        state, bounds = self.initialize_optimizer(state)
        X = self.dict2array(state)
        keys = list(state.keys())
        res = differential_evolution(func=self.cost_array,
                   bounds=bounds,
                   args = (keys, cost),
                   strategy=params['strategy'],
                   tol = params['tol'],
                   mutation = params['mutation'],
                   recombination = params['recombination'],
                   popsize = params['popsize'])
        # res = differential_evolution(func=self.cost_array,
        #                               bounds=bounds,
        #                               args = (keys, cost),
        #                               recombination = params['recombination'],
        #                               popsize = int(params['popsize']))
        if params['plot']:
            self.plot_optimization(lbl = params['strategy'])
        return None, None

    # ''' Hyperparameter optimization '''
    # def hypercost(self, params, args):
    #     ''' Returns the optimization time for a given algorithm, cost, and initial state '''
    #     algo, state, cost = args
    #     algo(state, cost, params)
    #     c = self.history.index[-1]-self.history.index[0]
    #     return c
    #
    # @algorithm
    # def grid_hypertune(self, state, cost, params={'steps':10},update=None):
    #     algo = self.differential_evolution
    #     hyperparams = {'popsize':15, 'recombination':0.7}
    #     bounds = np.array([[10,20],[0.3,1]])
    #     args = (algo, state, cost)
    #     points, costs = self.grid_sampling(hyperparams, self.hypercost, params['steps'], bounds, args=args, norm=False, update = update)
    #
    #     self.plot_2D(points,costs)
    #
    #     return points, costs

    ''' Visualization methods '''
    def plot_2D(self, points, costs):
        ''' Interpolates and plots a cost function sampled at an array of points. '''
        plt.figure()
        ordinate_index = 0
        abscissa_index = 1
        ordinate_mesh, abscissa_mesh = np.meshgrid(points[:,ordinate_index], points[:, abscissa_index])
        normalized_costs = -1*(costs - np.min(costs))/(np.max(costs)-np.min(costs)) + 1
        cost_grid = griddata(points[:,[ordinate_index, abscissa_index]], normalized_costs, (ordinate_mesh,abscissa_mesh))
        plot = plt.pcolormesh(ordinate_mesh, abscissa_mesh, cost_grid, cmap='gist_rainbow')
        plt.colorbar(plot)
        plt.savefig('driftmesh' + str(time.time()) + '.png')
        ax = plt.gca()

        return ax

    def plot_optimization(self, func=None, lbl = None, yscl = 'linear',
                          ylbl = 'Optimization Function', xlbl = 'Time (s)'):
        ''' Plots an optimization time series stored in self.history. '''
        if func is None:
            func = self.history
            func.index -= func.index[0]
        plt.plot(func['cost'], label = lbl)
        plt.yscale(yscl)
        plt.ylabel(ylbl)
        plt.xlabel(xlbl)
        plt.legend()
        plt.show()
