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
from scipy.optimize import curve_fit, minimize
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-2]))
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, WhiteKernel
from sklearn.decomposition import PCA, IncrementalPCA, KernelPCA
from sklearn.cluster import KMeans
import pandas as pd
import time
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn

class Optimizer():
    def __init__(self, noise=0):
        self.noise = noise

    ''' Base Functions '''
    def actuate(self, point):
        ''' Trivial placeholder actuate function which is overwritten by inheriting Hubs. '''
        self.state = point

    def cost(self, X = None, axes = None):
        ''' A gaussian cost function in N dimensions which is overwritten by inheriting Hubs. '''
        self.actuate(self.unnormalize(X, axes), axes)
        X = np.atleast_2d(X)

        cost = 1
        sigma = 1/3
        for n in range(X.shape[1]):
            cost *= np.exp(-(X[:,n]-0.5)**2/(2*sigma**2))
        cost += np.random.normal(0,self.noise)
        self.history.loc[time.time()] = -cost
        return -cost

    def plot_optimization(self, func=None, lbl = None, yscl = 'linear',
                          ylbl = 'Optimization Function', xlbl = 'Time (s)'):
        ''' Plots an optimization time series stored in a pandas Series. '''
        if func is None:
            func = self.history
            func.index -= func.index[0]
        plt.plot(func, label = lbl)
        plt.yscale(yscl)
        plt.ylabel(ylbl)
        plt.xlabel(xlbl)
        plt.legend()
        plt.show()

    ''' Optimization Routines and Algorithms '''
    def unnormalize(self, state, axes = None):
        ''' Converts normalized (0-1) state to physical state based on specified
            max and min parameter values. '''
        if axes == None:
            return self.min + state * (self.max - self.min)
        else:
            return self.min[[axes]] + state * (self.max[[axes]]-self.min[[axes]])

    def initialize_optimizer(self, axes = None):
        ''' Prepares a normalized substate and appropriate bounds. '''
        cols = []
        for axis in axes:
            cols.append('X' + str(axis))
        cols.append('cost')
        self.history = pd.DataFrame(index = [], columns = cols) #pd.Series(index=[])

        X = self.state
        if axes is not None:
            X = (X[[axes]] - self.min[[axes]])/(self.max[[axes]]-self.min[[axes]])
        else:
            X = (X - self.min)/(self.max-self.min)

        bounds = np.array(list(itertools.repeat([0,1], len(X))))

        return X, bounds

    def line_search(self, X = None, axis = 0, actuate = None, cost = None, step = 0.1):
        ''' Searches a single axis/dimension for a minimum using a moving derivative. '''
        X, bounds = self.initialize_optimizer(axis)

        #first compute the gradient to check which direction to move
        init_step = 5 * step
        init_points = []

        X[axis] -= init_step
        init_points.append(self.cost(X, axis))

        for i in range(2):
            X[axis] += init_step
            init_points.append(self.cost(X, axis))

        dir = -1*np.sign(np.mean(np.diff(init_points))) #determine direction from differences towards mininum

        if dir is -1: #undo move in wrong direction
            X[axis] -= init_step
            self.actuate(X)

        #now, perform the line search
        num_points = 5 #for moving derivative and to keep track of historically
        costs = []
        lastNPoints = np.array([])
        movingDeriv = 0
        maximizing = True

        while maximizing:
            X[axis] += dir*step
            val = self.cost(X, axis)
            costs.append(val)
            lastNPoints = np.append(lastNPoints, val)
            if len(lastNPoints) > num_points:
                lastNPoints = np.delete(lastNPoints,0)
            if len(lastNPoints) > 1:
                movingDeriv = np.mean(np.diff(lastNPoints))
            if movingDeriv > 0 and len(lastNPoints) == num_points:
                maximizing = False
                numSteps = len(lastNPoints) - np.argmin(lastNPoints) - 1
                X[axis] -= dir*step*numSteps
                costs.append(self.cost(X, axis))

        return X, costs

    def grid_search(self, X = None, axes = None, actuate = None, cost = None,
                    plot = False, steps = 10):
        ''' An N-dimensional grid search routine with optional plotting. '''
        X, bounds = self.initialize_optimizer(axes)
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
            costs.append(self.cost(point, axes))

        ''' Plot result if desired '''
        ax = None
        if plot and len(X) is 2:
            ordinate_index = 0
            abscissa_index = 1
            ordinate_mesh, abscissa_mesh = np.meshgrid(points[:,ordinate_index], points[:, abscissa_index])
            print(ordinate_mesh.shape)
            print(abscissa_mesh.shape)
            cost_grid = griddata(points[:,[ordinate_index, abscissa_index]], cost, (ordinate_mesh,abscissa_mesh))
            plot = plt.pcolormesh(ordinate_mesh, abscissa_mesh, cost_grid, cmap='gist_rainbow')
            plt.colorbar(plot)
            ax = plt.gca()

        best_point = points[np.argmin(costs)]
        self.actuate(self.unnormalize(best_point, axes), axes)

        return points, costs, ax

    def gaussian_process_next_sample(self, X, bounds, b, cost, gaussian_process,
                                     greater_is_better=False, restarts=25):
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

    def effective_cost(self, x, b, gp):
        ''' Computes an effective cost for Gaussian process optimization, featuring
            some tradeoff between optimization and learning. '''
        ''' Watch for function recieveing a 2d x with higher dimensional state vectors (disagreement with internal GP dimension) '''
        mu, sigma = gp.predict(np.atleast_2d(x), return_std = True)
       # return (b*mu+np.sqrt(1-b**2)*sigma)
        return b*mu-(1-b)*sigma

    def gaussian_process(self, X = None, axes = None, actuate = None, cost = None, iterations = 10, plot = False):
        ''' Gaussian Processing from https://github.com/thuijskens/bayesian-optimization/blob/master/python/gp.py
            and https://www.nature.com/articles/srep25890.pdf '''
        if cost is None:
            cost = self.cost
        X, bounds = self.initialize_optimizer(axes)
        c = np.array([cost(X, axes=axes)])

        points, costs = self.random_sampling(cost, 15, bounds, axes=axes)
        X = np.append(np.atleast_2d(X), points, axis=0)
        c = np.append(c, costs)
        kernel = C(1.0, (1e-3, 1e3)) * RBF(10, (1e-2, 1e2))
        self.gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10)
        for i in range(iterations):
            self.gp.fit(X,c)
            b = i / (iterations-1) #= 0.5 + 0.5*np.cos(2*np.pi*i/(iterations-1)), =1
            X_new = self.gaussian_process_next_sample(X, bounds, b, self.effective_cost, self.gp, greater_is_better=False, restarts=10)
            X_new = np.atleast_2d(X_new)
            X = np.append(X, X_new, axis=0)
            c = np.append(c, self.cost(X[-1], axes = axes))
        self.actuate(self.unnormalize(X[np.argmin(c)], axes), axes)
        if plot:
            self.plot_optimization(func = c, lbl = 'Gaussian Processing')

        return X, c

    def random_sampling(self, cost, N, bounds, axes=None):
        ''' Performs a random sampling of the cost function at N points within the specified bounds. '''
        points = np.random.uniform(size=(N,bounds.shape[0]))
        c = []
        for point in points:
            c.append(cost(point,axes=axes))

        return points, c

    def skl_minimize(self, cost, method = 'L-BFGS-B', X = None, axes = None, plot = False):
        ''' Runs a specified scikit-learn minimization method on the target axes and cost. '''
        X, bounds = self.initialize_optimizer(axes)
        res = minimize(fun=cost,
                   x0=X,
                   bounds=bounds,
                   method=method,
                   args=(axes))
        #simplex for SKL is res = minimize(fun = cost,x0 = X.reshape(1, -1), method = 'Nelder-Mead', tol = 1e7)
        print("SKL:" + method + "=%s" % res)
        if plot:
            self.plot_optimization(lbl = method)

    #possible to make a dictionary for these optimization methods and all possibile SKL optimize.minimze routines
    def optimize(self, routines = ['gp'], X = None, axes = None, iterations = 20, plot = True,
                 actuate = None, cost = None, span = 1, steps = 100, dither = 0.1, eta = 1, method = 'L-BFGS-B'):
        ''' Runs a targeted optimization routine with a given axes list and cost. '''
        for r in routines:
            X = np.random.uniform(0, 1, size=(1,self.dim)) #change when axes is implemented
            if r == 'gp' or routines == ['all']:
                X, cost, points, c_pred = self.gaussian_process(X, axes, iterations = iterations, plot = plot)
                print("Gaussian Processing=%s" % cost[-1])
            if r == 'sklm' or routines == ['all']:
                self.skl_minimize(cost = cost, method = method)
            if r == 'gs' and routines == ['all']:
                c = self.grid_search(plot = plot)
                print("Grid Search=%s" % c[-1])

    ''' Dimensionality Analytics and Reduction Algorithms (X always being the training data set) '''
    #NOTE: might need to convert to something with COST and to the entire training database
    #use differential evolution from skl to develop a dataset for the pca to determine reduction, caluclate covariance and perform pca on it

    def extract_pcs(self, X = None):
        ''' Uses numpy's svd() function to obtain the principal components of the training set. '''
        #NOTE: must take step to recenter data around the origin as necessary here
        X_centered = X - X.mean(axis = 0) #NOTE: assumes that the dataset is centered around the origin
        U, s, Vt = np.linalg.svd(X_centered)
        #use the following to extract each pca given their index: c1 = Vt.T[:,0] where 0 is the index
        return Vt

    def pca_reduction(self, X = None, pvariance = 0.95, slvr = "auto"): #svd_solver can be ‘auto’, ‘full’, ‘arpack’, or ‘randomized’
        '''Employs SKL's PCA to reduce dimensionality of the dataset based on a preserved variance threshold. '''
        if pvariance is not int(pvariance):
            pca = PCA()
            pca.fit(X.copy)
            d = np.argmax(np.cumsum(pca.explained_variance_ratio_) >= pvariance) + 1
            print("Minimum number of dimensions to preserve variance: ", d)

        #reduce the data set and find the breakdown of variance for each axis in the dataset
        #define pvariance as a number of components or percentage of varaiance to preserve (e.g. pvariance = 3 or 0.95)
        pca = PCA(n_components = pvariance, svd_solver = slvr) #use "randomized" for solver if desiring stochastic approximations
        X_reduced = pca.fit_tranform(X)
        variance_breakdown = pca.explained_variance_ratio_
        return X_reduced, variance_breakdown

    def pca_kernel(self, X = None, n_comps = 4, krnl = "rbf", gma = 0.04):
        '''Employs kernel techniques to PCA, allowing complex nonlinear projections for dimensionality reduction. '''
        rbf_pca = KernelPCA(n_components = n_comps, kernel = krnl, gamma = gma)
        X_reduced = rbf_pca.fit_transform(X)
        return X_reduced

#    def cluster(self, X = None, n_clusters):
#        kmeans = KMeans(n_clusters=4).fit(X)
#        cluster_labels = kmeans.labels_
#        return kmeans, cluster_labels

    # def covariance_reduction(self, X = None):
    #     '''with a 13 dimensional array, use covariance on the original data set,
    # rows = number of features, columns = number of observations, covariance
    # yields number of rows = number of columns, then feature extraction using
    # PCA or clustering algorithm '''

if __name__ == '__main__':
    SNR = 100
    a = Optimizer(noise = 1/SNR)
    a.dim = 4
    pos = np.random.uniform(0, 1, size=(1, a.dim)) #np.ones(dim)*X0, X0 = 0.2
    a.actuate(pos)
    a.optimize(routines = ['gs'])
