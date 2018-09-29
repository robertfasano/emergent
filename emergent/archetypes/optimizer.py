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
# from algorithms.neural_network import NeuralNetwork
from sklearn import metrics
import pandas as pd
import time
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn
from emergent.utility import methodsWithDecorator, algorithm

class Optimizer():
    ''' General methods '''
    def __init__(self, control_node):
        ''' Initialize the optimizer and link to the parent Control node. '''
        self.parent = control_node
        self.actuate = self.parent.actuate

    ''' State conversion functions '''
    def array2dict(self, arr, initial):
        ''' Converts the array back to the form of the initial object. '''
        initial_type = self.sequence_or_state(initial)
        # initial_type = 'state'
        if initial_type == 'sequence': # deprecated
            target = self.array2sequence(arr, initial)
        elif initial_type =='state':
            target = self.array2state(arr, initial)

        return target

    def array2sequence(self, arr, sequence):
        ''' Updates setpoints in a sequence with values from an array. '''
        # deprecated
        i = 0
        for key in sequence.keys():
            s = sequence[key]
            for j in range(len(s)):
                s[j][1] = arr[i]
                i += 1
        return sequence

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

    def cost_from_array(self, arr, d, cost):
        ''' Converts the array back to the form of d (e.g. sequence or state),
            unnormalizes it, and returns cost evaluated on the result. '''
        target = self.array2dict(arr, d)
        target = self.unnormalize(target)

        c = cost(target)

        ''' Update history '''
        t = time.time()
        type = self.sequence_or_state(target)
        if type == 'sequence':
            for key in target.keys():
                s = target[key]
                for i in range(len(s)):
                    col = key+str(i)
                    self.history.loc[t,col] = s[i][1]
        self.history.loc[t,'cost']=-c
        return c

    def dict2array(self, d):
        d_type = self.sequence_or_state(d)

        if d_type == 'sequence':
            arr = self.sequence2array(d)
        elif d_type == 'state':
            arr = self.state2array(d)

        return arr

    def sequence2array(self, sequence):
        ''' Convert an experimental sequence to an array of setpoints. '''
        arr = []
        for key in sequence.keys():
            s = sequence[key]
            for i in range(len(s)):
                arr.append(s[i][1])
        return arr

    def sequence_or_state(self, d):
        d_type = type(list(d.values())[0])
        if d_type is list:
            return 'sequence'
        else:
            return 'state'

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

    def initialize_optimizer(self, state):
        ''' Creates a history dataframe to log the optimization. Normalizes the
            state in terms of the min/max of each Input node, then prepares a
            bounds array. '''
        initial_type = self.sequence_or_state(state)
        if initial_type == 'state':
            num_items = 0
            cols = []
            for dev in state:
                for input in state[dev]:
                    cols.append(dev+'.'+input)
                    num_items += 1
            state = self.normalize(state)
            cols.append('cost')
            self.history = pd.DataFrame(columns=cols)
            bounds = np.array(list(itertools.repeat([0,1], num_items)))
            state = self.dict2array(state)
            return state, bounds

        elif initial_type == 'sequence':
            # deprecated
            cols = []
            for key in state.keys():
                sequence = state[key]
                for i in range(len(sequence)):
                    cols.append(key+str(i))
            cols.append('cost')
            self.history = pd.DataFrame(index = [], columns = cols)

            state = self.normalize(state)
            state = self.dict2array(state)
            bounds = np.array(list(itertools.repeat([0,1], len(state))))
            return state, bounds

    def list_algorithms(self):
        ''' Returns a list of all methods tagged with the '@algorithm' decorator '''
        return methodsWithDecorator(Optimizer, 'algorithm')

    def normalize(self, unnorm):
        ''' Normalizes a state or substate based on min/max values of the Inputs,
            saved in the parent Control node. '''
        type = self.sequence_or_state(unnorm)
        norm = {}

        for dev in unnorm:
            norm[dev] = {}
            for i in unnorm[dev]:
                min = self.parent.settings[dev][i]['min']
                max = self.parent.settings[dev][i]['max']
                if type == 'state':
                    norm[dev][i] = (unnorm[dev][i] - min)/(max-min)
                elif type == 'sequence':        # deprecated
                    s = unnorm[i]
                    s_norm = []
                    for j in range(len(s)):
                        s_norm.append([s[j][0], (s[j][1] - min)/(max-min)])
                    norm[i] = s_norm
        return norm

    def unnormalize(self, norm):
        ''' Converts normalized (0-1) state to physical state based on specified
            max and min parameter values. '''
        type = self.sequence_or_state(norm)
        unnorm = {}
        for dev in norm:
            unnorm[dev] = {}
            for i in norm[dev]:
                min = self.parent.settings[dev][i]['min']
                max = self.parent.settings[dev][i]['max']
                if type == 'state':
                    unnorm[dev][i] = min + norm[dev][i] * (max-min)
                elif type == 'sequence':    # deprecated
                    s = norm[i]
                    s_unnorm = []
                    for j in range(len(s)):
                        s_unnorm.append([s[j][0], min+s[j][1]*(max-min)])
                    unnorm[i] = s_unnorm
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

    def grid_sampling(self, state, cost, points, evaluations_per_point, update=None, args=None, norm = True):
        ''' Performs a uniformly-spaced sampling of the cost function in the
            space spanned by the passed-in state dict. '''
        arr, bounds = self.initialize_optimizer(state)
        N = len(arr)
        grid = []
        for n in range(N):
            space = np.linspace(bounds[n][0], bounds[n][1], points)
            grid.append(space)
        grid = np.array(grid)
        points = np.transpose(np.meshgrid(*[grid[n] for n in range(N)])).reshape(-1,N)

        ''' Actuate search '''
        costs = []
        for point in points:
            acquisitions = []
            for i in range(evaluations_per_point):
                c = self.cost_from_array(point, state, cost)
                acquisitions.append(c)
            costs.append(np.mean(acquisitions))
            if update is not None:
                update(len(costs)/len(points))

        points = np.array(points)
        costs = np.array(costs)

        return points, costs

    def random_sampling(self,state, cost, points, bounds):
        ''' Performs a random sampling of the cost function at N points within
            the specified bounds. '''
        points = np.random.uniform(size=(points,len(state.keys())))
        costs = []
        for point in points:
            target = self.array2dict(point, state)
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
    @algorithm
    def grid_search(self, state, cost, params={'steps':10, 'evaluations_per_point':1}, update=None):
        ''' An N-dimensional grid search (brute force) optimizer. '''
        arr, bounds = self.initialize_optimizer(state)
        ''' Generate search grid '''
        points, costs = self.grid_sampling(state, cost, params['steps'], params['evaluations_per_point'], update=update)

        ''' Plot result if desired '''
        ax = None
        if params['plot']:
            limits = {}
            for dev in state:
                for name in state[dev]:
                    full_name = name+'.'+dev
                    limits[full_name] = {}
                    limits[full_name]['min'] = self.parent.settings[dev][name]['min']
                    limits[full_name]['max'] = self.parent.settings[dev][name]['max']
            ax = self.plot_2D(points, costs, limits = limits, save=params['save'])
        best_point = self.array2dict(points[np.argmin(costs)], state)
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
    def gaussian_process(self, state, cost, params={'batch_size':10,'presampled': 15, 'iterations':10},update=None):
        ''' Online Gaussian process regression. Batch sampling is done with
            points with varying trade-off of optimization vs. exploration. '''
        X, bounds = self.initialize_optimizer(state)
        c = np.array([self.cost_from_array(X, state,cost)])

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
                c = np.append(c, self.cost_from_array(X[-1], state, cost))
                if update is not None:
                    update((j+i*params['batch_size'])/params['batch_size']/params['iterations'])
        best_point = self.array2state(X[np.argmin(c)], state)
        self.actuate(self.unnormalize(best_point))
        if params['plot']:
            self.plot_optimization(lbl = 'Gaussian Processing')

        self.parent.save(tag='optimize', save=params['save'])

        return X, c


    @algorithm
    def scipy_minimize(self, state, cost, params={'method':'L-BFGS-B', 'tol':1e-7}, update=None):
        ''' Runs a specified scipy minimization method on the target axes and cost. '''
        arr, bounds = self.initialize_optimizer(state)
        keys = list(state.keys())
        res = minimize(fun=self.cost_from_array,
                   x0=arr,
                   bounds=bounds,
                   args = (state, cost),
                   method=params['method'],
                   tol = params['tol'])
        if params['plot']:
            self.plot_optimization(lbl = params['method'], save=params['save'])

        self.parent.save(tag='optimize')

        return None, None

    @algorithm
    def simplex(self, state, cost, params={'tol':4e-3}, update=None):
        ''' Nelder-Mead algorithm from scipy.optimize. '''
        X, bounds = self.initialize_optimizer(state)
        res = minimize(fun=self.cost_from_array,
                   x0=X,
                   args = (state, cost),
                   method='Nelder-Mead',
                   tol = params['tol'])

        if params['plot']:
            self.plot_optimization(lbl = 'simplex', save=params['save'])

        self.parent.save(tag='optimize')

        return None, None

    @algorithm
    def differential_evolution(self, state, cost, params={'strategy':'best1bin', 'popsize':15, 'tol':0.01, 'mutation': 1,'recombination':0.7}, update=None):
        ''' Differential evolution algorithm from scipy.optimize. '''
        X, bounds = self.initialize_optimizer(state)
        keys = list(state.keys())
        res = differential_evolution(func=self.cost_from_array,
                   bounds=bounds,
                   args = (state, cost),
                   strategy=params['strategy'],
                   tol = params['tol'],
                   mutation = params['mutation'],
                   recombination = params['recombination'],
                   popsize = params['popsize'])
        if params['plot']:
            self.plot_optimization(lbl = params['strategy'], save=params['save'])

        self.parent.save(tag='optimize')

        return None, None

    # @algorithm
    # def neural_network(self, state, cost, params={'layers':10, 'neurons':64, 'optimizer':'adam', 'activation':'erf', 'initial_points':100, 'cycles':500, 'samples':1000}, update = None):
    #     X, bounds = self.initialize_optimizer(state)
    #     norm_state = self.array2state(X,state)
    #     NeuralNetwork(self, norm_state, cost, bounds, params=params, update = update)
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
    def plot_2D(self, points, costs, normalized_cost = False, limits = None,
                save = False, color_map='viridis_r'):
        ''' Interpolates and plots a cost function sampled at an array of points. '''
        plt.figure()
        points = points.copy()
        ordinate_index = 0
        abscissa_index = 1
        if limits is not None:
            names = list(limits.keys())
            for i in [0,1]:
                points[:,i] = limits[names[i]]['min'] + points[:,i]*(limits[names[i]]['max']-limits[names[i]]['min'])
        ordinate_mesh, abscissa_mesh = np.meshgrid(points[:,ordinate_index], points[:, abscissa_index])
        normalized_costs = -1*(costs - np.min(costs))/(np.max(costs)-np.min(costs)) + 1
        if normalized_cost:
            cost_grid = griddata(points[:,[ordinate_index, abscissa_index]], normalized_costs, (ordinate_mesh,abscissa_mesh))
        else:
            cost_grid = griddata(points[:,[ordinate_index, abscissa_index]], costs, (ordinate_mesh,abscissa_mesh))
        plot = plt.pcolormesh(ordinate_mesh, abscissa_mesh, cost_grid, cmap=color_map)
        plt.colorbar(plot)
        if save:
            plt.savefig(self.parent.data_path + str(time.time()) + '.png')
        ax = plt.gca()
        if limits is not None:
            plt.xlabel(names[0])
            plt.ylabel(names[1])

        return ax

    def plot_optimization(self, func=None, lbl = None, yscl = 'linear',
                          ylbl = 'Optimization Function', xlbl = 'Time (s)', save = False):
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
        if save:
            plt.savefig(self.parent.data_path + str(time.time()) + '.png')

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

    def animate_sequence_history(self):
        for i in range(len(self.history)):
            if not i%12:
                self.plot_history_slice(i)
