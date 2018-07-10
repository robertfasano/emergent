''' This script implements an Aligner class from which many devices inherit methods such as:
    persistent positioning, first light acquisition, and realtime optimization
'''
''' TODO:
        - sampleRange/dither etc should be arrays to allow multi-device alignment
        - MasterAligner takes a number of aligners in __init__ and can access their individual actuate functions; store position indices for each device
        - MasterAligner class should overload actuate to route signals to each device, e.g.:
                mems.moveTo[point[3:6]]
                agilis.actuate[point[6:9]]
        - MasterAligner.actuate should be threaded
        - take a state vector, decompose it into substates, run optimizations in series of separate substates
'''
import numpy as np
import itertools
import sys
import os
import time
from scipy.interpolate import griddata
from scipy.stats import norm
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit, minimize
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-2]))
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, WhiteKernel
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn

class Optimizer():
    def __init__(self):
        self.plot = plt.figure() # figure for all optimization routine graphing
        self.noise = 0

    ''' Base functions '''
    def actuate(self, point):
        self.state = point

    def cost(self, X = None, axes = None):
        ''' A gaussian cost function in N dimensions. Overload in child classes with appropriate function '''
        self.actuate(self.unnormalize(X, axes), axes)
        X = np.atleast_2d(X)

        cost = 1
        sigma = 1/3
        for n in range(X.shape[1]):
            cost *= np.exp(-X[:,n]**2/(2*sigma**2))
        cost += np.random.normal(0,self.noise)

        return -cost

    ''' Optimization Routines and Algorithms '''
    def unnormalize(self, state, axes = None):
        if axes == None:
            return self.min + state * (self.max - self.min)
        else:
            return self.min[[axes]] + state * (self.max[[axes]]-self.min[[axes]])

    def initialize_optimizer(self, X = None, axes = None):
        ''' Prepares a normalized substate and appropriate bounds '''
        if X is None and axes is None:
            X = self.state
        elif X is None:
            X = self.state[[axes]]
        if axes is not None:
            X = (X[[axes]] - self.min[[axes]])/(self.max[[axes]]-self.min[[axes]])
        else:
            X = (X - self.min)/(self.max-self.min)

        bounds = np.array(list(itertools.repeat([0,1], len(X))))

        return X, bounds

    def grid_search(self, X = None, axes = None, actuate = None, cost = None,
                    plot = False, steps = 10):
        ''' An N-dimensional grid search routine '''
        X, bounds = self.initialize_optimizer(X, axes)
        ''' Generate search grid '''
        N = len(X)
        grid = []
        for n in range(N):
            space = np.linspace(bounds[n][0], bounds[n][1], steps)
            grid.append(space)
        grid = np.array(grid)
        points = np.transpose(np.meshgrid(*[grid[n] for n in range(N)])).reshape(-1,N)

        ''' Actuate search '''
        costs = []
        for point in points:
            costs.append(cost(point, axes))

        ''' Plot result if desired '''
        if plot:
            if len(X) == 2 and axes == None:
                ordinate_index = 0
                abscissa_index = 1
            else:
                ordinate_index = axes[0]
                abscissa_index = axes[1]
            ordinate_mesh, abscissa_mesh = np.meshgrid(points[:,ordinate_index], points[:, abscissa_index])
            cost_grid = griddata(points[:,[ordinate_index, abscissa_index]], cost, (ordinate_mesh,abscissa_mesh))
            plot = plt.pcolormesh(ordinate_mesh, abscissa_mesh, cost_grid, cmap='gist_rainbow')
            plt.colorbar(plot)

        best_point = points[np.argmin(costs)]
        self.actuate(self.unnormalize(best_point, axes), axes)

        return points, costs

    def gaussian_process_next_sample(self, X, bounds, b, acquisition_func, gaussian_process,
                                     greater_is_better=False, restarts=25):
        best_x = None
        best_acquisition_value = 1

        for starting_point in np.random.uniform(bounds[0][0], bounds[0][1], size=(restarts, X.shape[1])):
            res = minimize(fun=acquisition_func,
                       x0=starting_point.reshape(1, -1),
                       bounds=bounds,
                       method='L-BFGS-B',
                       args=(b, gaussian_process))
            if res.fun < best_acquisition_value:
                best_acquisition_value = res.fun
                best_x = res.x

        return best_x

    def effective_cost(self, x, b, gp):
        ''' The problem: even with a 3d state vector, this function was receiving
            a 2d x, which disagreed with the internal dimension of the GP. '''
        mu, sigma = gp.predict(np.atleast_2d(x), return_std = True)
        return -(b*mu+np.sqrt(1-b**2)*sigma)

    def gaussian_process(self, X = None, axes = None, actuate = None, cost = None,
                    iterations = 10, plot = False, span = 10, steps = 100, random_search = False):
        ''' Gaussian Processing from https://github.com/thuijskens/bayesian-optimization/blob/master/python/gp.py
            and https://www.nature.com/articles/srep25890.pdf '''
        ''' Integrated with Lab of Things: method now uses actuate() to update the
            actual state instead of just changing X. This is currently implemented
            by making self.cost() measure at the current state if X is not specified,
            and otherwise actuate to X then measure. '''
        if cost is None:
            cost = self.cost
        X, bounds = self.initialize_optimizer(X, axes)
        N = len(X)
        c = np.array([cost(X, axes=axes)])
        kernel = C(1.0, (1e-3, 1e3)) * RBF(10, (1e-2, 1e2))
        self.gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10)
        X_new = np.random.uniform(bounds[0][0], bounds[0][1], size=(1, len(X)))
        for i in range(iterations):
            X = np.append(np.atleast_2d(X), np.atleast_2d(X_new), axis=0)
            X = X.reshape(-1,N)
            c = np.append(c, self.cost(X[-1], axes = axes))

            self.gp.fit(X,c)

            b = np.cos(2*np.pi*i/(iterations-1))
            X_new = self.gaussian_process_next_sample(X, bounds, b, self.effective_cost, self.gp, greater_is_better=False, restarts=10)
        self.actuate(self.unnormalize(X[-1], axes), axes)
        if plot:
            self.plot_optimization(func = c, lbl = 'Gaussian Processing')

        return X, c

    def plot_optimization(self, func, lbl = None, yscl = 'log',
                          ylbl = 'Optimization Function', xlbl = 'Iteration #'):
            plt.plot(func, label = lbl)
            plt.yscale(yscl)
            plt.ylabel(ylbl)
            plt.xlabel(xlbl)
            plt.legend()

    def skl_minimize(self, cost, method = 'L-BFGS-B', X = None, axes = None):
        X, bounds = self.initialize_optimizer(X, axes)
        res = minimize(fun=cost,
                   x0=X,
                   bounds=bounds,
                   method=method,
                   args=(axes))
        print(res)

    def optimize(self, routines = ['gp'], X = None, axes = None, iterations = 20, plot = True,
                 actuate = None, cost = None, span = 1, steps = 100, dither = 0.1, eta = 1):
#        if axes == None:   #set the indices that the user would like to specify for each optimization routine
#            axes = [0, self.dim]

        for r in routines:
            X = np.random.uniform(0, 1, size=(1,self.dim)) #change when axes is implemented
            if r == 'gp' or routines == ['all']:
                X, cost, points, c_pred = self.gaussian_process(X, axes, iterations = iterations, plot = plot,
                                                                span = span, steps = steps)
                print("Gau$$ian Proce$$ing=%s" % cost[-1])
                '''unstable as of now - able to take a set of axes isolated from position
                standardized all parameter orders and names across all optimization functions
                isolated local variables to X instead of self.state such that actuations can be unique to methods
                plot optimization general method
                optimize general method for iterative series optimization or flexible ensemble optimization routines
                POSSIBLE TO ADD a dictionary for these optimization methods and all possible scikit-learn optimize.minimize routines
                '''
            if r == 'skl_splx' or routines == ['all']:
                X2 = self.skl_simplex(X, axes, iterations = iterations, plot=plot)
                print("Scikit-Learn Simplex=%s" % X2[0])
            if r == 'rf_splx' or routines == ['all']:
                h, c = self.rjf_simplex(X, axes, iterations = iterations, plot = plot)
                print("RJF Simplex=%s" % c[-1])
            if r == 'gd' or routines == ['all']:
                h, c = self.gradient_descent(X, axes, iterations = iterations, plot = plot, d = dither, eta = 1)
                print("Gradient Descent=%s" % c[-1][-1])
            if r == 'gs':  #WARNING - plotting grid search does not work
                c = self.grid_search(X, axes = [0,1] ,plot = plot,  span = span, steps = steps)
                print("Grid Search=%s" % c[-1])

if __name__ == '__main__':
    a = Optimizer()
    a.dim = 4
    X0 = .2
    SNR = 100
    a.noise = 1/SNR
    pos = np.ones(a.dim)*X0
    pos = np.random.uniform(0, 1, size=(1,a.dim))
    a.position = pos
    #plt.title(r'Function optimization from %f, d=%i, SNR=%i'%(X0,a.dim, SNR))

    print('Optimization Results')
    a.optimize(routines = ['all'])
