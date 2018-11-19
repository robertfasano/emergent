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
plt.ion()
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
from emergent.utility import methodsWithDecorator, algorithm
from copy import deepcopy

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

    def callback(self, *args):
        return self.active

    def log(self, filename):
        ''' Saves the results of the optimization to file with the given name '''
        self.history.to_csv(self.parent.data_path+filename+'.csv')

    def terminate(self):
        self.active = False

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
        return points, costs

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
    def _cost(self, state, cost):
        ''' Unnormalizes the state dict, computes the cost, and logs. '''
        c = cost(self.unnormalize(state))
        self.history.loc[time.time()] = -c
        return c

    def initialize_optimizer(self, state, cost, params, cost_params):
        ''' Creates a history dataframe to log the optimization. Normalizes the
            state in terms of the min/max of each Input node, then prepares a
            bounds array. '''
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


    ''' Sampling methods '''
    def sample(self, state, cost, cost_params, method='random_sampling', points = 1, bounds = None):
        ''' Returns a list of points sampled with the specified method, as well as
            the cost function evaluated at these points. '''
        if bounds is None:
            bounds = np.array(list(itertools.repeat([0,1], len(state.keys()))))
        func = getattr(self, method)
        points, cost = func(state, cost, cost_params, points, bounds)

        return points, cost

    def grid_sampling(self, state, cost, params, cost_params, points,  args=None, norm = True, callback = None):
        ''' Performs a uniformly-spaced sampling of the cost function in the
            space spanned by the passed-in state dict. '''
        if callback is None:
            callback = self.callback
        arr, bounds = self.initialize_optimizer(state, cost, params, cost_params)
        N = len(arr)
        grid = []
        for n in range(N):
            space = np.linspace(bounds[n][0], bounds[n][1], points)
            grid.append(space)
        grid = np.array(grid)
        points = np.transpose(np.meshgrid(*[grid[n] for n in range(N)])).reshape(-1,N)

        ''' Actuate search '''
        costs = np.array([])
        for point in points:
            if not callback():
                return points[0:len(costs)], costs
            c = self.cost_from_array(point, state, cost, cost_params)
            costs = np.append(costs, c)
            self.progress = len(costs) / len(points)

        # points = np.array(points)
        # costs = np.array(costs)

        return points, costs

    def random_sampling(self,state, cost, cost_params, points, bounds, callback = None):
        ''' Performs a random sampling of the cost function at N points within
            the specified bounds. '''
        if callback is None:
            callback = self.callback
        dof = sum(len(state[x]) for x in state)
        points = np.random.uniform(size=(points,dof))
        costs = []
        for point in points:
            if not callback():
                return points[0:len(costs)], costs
            c = self.cost_from_array(point, state, cost, cost_params)
            costs.append(c)

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
    @algorithm
    def grid_search(self, state, cost, params={'steps':10}, cost_params = {}):
        ''' An N-dimensional grid search (brute force) optimizer. '''
        arr, bounds = self.initialize_optimizer(state, cost, params, cost_params)
        ''' Generate search grid '''
        points, costs = self.grid_sampling(state, cost, params, cost_params, params['steps'])

        best_point = self.array2state(points[np.argmin(costs)], state)
        self.actuate(self.unnormalize(best_point))
        self.progress = 1
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
    def gaussian_process(self, state, cost, params={'presampled points': 15, 'iterations':10, 'batch size':10, 'kernel amplitude': 1, 'kernel length scale': 1, 'kernel noise': 0.1}, cost_params = {}, callback = None):
        ''' Online Gaussian process regression. Batch sampling is done with
            points with varying trade-off of optimization vs. exploration. '''
        if callback is None:
            callback = self.callback
        X, bounds = self.initialize_optimizer(state, cost, params, cost_params)
        c = np.array([self.cost_from_array(X, state,cost, cost_params)])
        points, costs = self.sample(state, cost, cost_params, 'random_sampling', params['presampled points'])
        X = np.append(np.atleast_2d(X), points, axis=0)
        c = np.append(c, costs)
        kernel = C(params['kernel amplitude'], (1e-3, 1e3)) * RBF(params['kernel length scale'], (1e-2, 1e2)) + WhiteKernel(params['kernel noise'])
        self.gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10)
        for i in range(params['iterations']):
            if not callback():
                return points[0:len(costs)], costs
            self.gp.fit(X,c)
            a = i / (params['iterations']-1)        # scale from explorer to optimizer through iterations
            for j in range(params['batch size']):
                b = a * j / (params['batch size']-1)        # scale from explorer to optimizer throughout batch
                X_new = self.gp_next_sample(X, bounds, b, self.gp_effective_cost, self.gp, restarts=10)
                X_new = np.atleast_2d(X_new)
                X = np.append(X, X_new, axis=0)
                c = np.append(c, self.cost_from_array(X[-1], state, cost, cost_params))
                self.progress = (j+i*params['batch size'])/params['batch size']/params['iterations']
        best_point = self.array2state(X[np.argmin(c)], state)
        self.actuate(self.unnormalize(best_point))
        if params['plot']:
            self.plot_optimization(lbl = 'Gaussian Processing')     # plot trajectory
            ''' Predict and plot cost landscape '''
            grid = []
            N = X.shape[1]
            for n in range(N):
                space = np.linspace(bounds[n][0], bounds[n][1], 30)
                grid.append(space)
            grid = np.array(grid)
            predict_points = np.transpose(np.meshgrid(*[grid[n] for n in range(N)])).reshape(-1,N)
            predict_costs = np.array([])
            for point in predict_points:
                predict_costs = np.append(predict_costs, self.gp.predict(np.atleast_2d(point)))
            plot_2D(predict_points, predict_costs)
        self.progress = 1
        return X, c

    @algorithm
    def scipy_minimize(self, state, cost, params={'method':'L-BFGS-B', 'tol':1e-7}, cost_params = {}):
        ''' Runs a specified scipy minimization method on the target axes and cost. '''
        arr, bounds = self.initialize_optimizer(state, cost, params, cost_params)
        keys = list(state.keys())
        res = minimize(fun=self.cost_from_array,
                   x0=arr,
                   bounds=bounds,
                   args = (state, cost, cost_params),
                   method=params['method'],
                   tol = params['tol'])

        self.parent.save(tag='optimize')

        return None, None

    @algorithm
    def simplex(self, state, cost, params={'tol':4e-3}, cost_params = {}):
        ''' Nelder-Mead algorithm from scipy.optimize. '''
        X, bounds = self.initialize_optimizer(state, cost, params, cost_params)
        res = minimize(fun=self.cost_from_array,
                   x0=X,
                   args = (state, cost, cost_params),
                   method='Nelder-Mead',
                   tol = params['tol'])

        self.parent.save(tag='optimize')

        return None, None

    @algorithm
    def differential_evolution(self, state, cost, params={'strategy':'best1bin', 'popsize':15, 'tol':0.01, 'mutation': 1,'recombination':0.7}, cost_params = {}):
        ''' Differential evolution algorithm from scipy.optimize. '''
        X, bounds = self.initialize_optimizer(state, cost, params, cost_params)
        keys = list(state.keys())
        res = differential_evolution(func=self.cost_from_array,
                   bounds=bounds,
                   args = (state, cost, cost_params),
                   strategy=params['strategy'],
                   tol = params['tol'],
                   mutation = params['mutation'],
                   recombination = params['recombination'],
                   popsize = params['popsize'])

        self.parent.save(tag='optimize')

        return None, None

    # @algorithm
    # def neural_network(self, state, cost, params={'layers':10, 'neurons':64, 'optimizer':'adam', 'activation':'erf', 'initial_points':100, 'cycles':500, 'samples':1000}):
    #     X, bounds = self.initialize_optimizer(state, cost, params, cost_params)
    #     norm_state = self.array2state(X,state)
    #     NeuralNetwork(self, norm_state, cost, bounds, params=params)
    #
    #     return None, None

    # ''' Hyperparameter optimization '''
    # def hypercost(self, params, args):
    #     ''' Returns the optimization time for a given algorithm, cost, and initial state '''
    #     algo, state, cost = args
    #     algo(state, cost, params)
    #     c = self.history.index[-1]-self.history.index[0]
    #     return c
    #
    # @algorithm
    # def grid_hypertune(self, state, cost, params={'steps':10}):
    #     algo = self.differential_evolution
    #     hyperparams = {'popsize':15, 'recombination':0.7}
    #     bounds = np.array([[10,20],[0.3,1]])
    #     args = (algo, state, cost)
    #     points, costs = self.grid_sampling(hyperparams, self.hypercost, params['steps'], bounds, args=args, norm=False)
    #
    #     plot_2D(points,costs)
    #
    #     return points, costs

    ''' Control methods '''
    def PID(self, state, error, params={'proportional_gain':1, 'integral_gain':0, 'derivative_gain':0, 'sign':1}, error_params = {}, callback = None):
        self.initialize_optimizer(state, error, params, error_params)
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

        while callback():
            e = error(state, error_params)
            t = time.time()
            print(t)
            self.history.loc[t,'cost']=e
            for dev in state:
                for input in state[dev]:
                    self.history.loc[t,dev+'.'+input] = state[dev][input]
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
