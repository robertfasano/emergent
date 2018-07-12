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
'''
import numpy as np
import itertools
import sys
import os
from scipy.interpolate import griddata
from scipy.stats import norm
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit, minimize
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-2]))
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, WhiteKernel
from sklearn.decomposition import PCA, IncrementalPCA, KernalPCA
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn

class Optimizer():
    def __init__(self, noise=0):
        self.plot = plt.figure() # figure for all optimization routine graphing
        self.noise = noise

    ''' Base Functions '''
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

    def initialize_optimizer(self, axes = None):
        ''' Prepares a normalized substate and appropriate bounds '''
        X = self.state
        if axes is not None:
            X = (X[[axes]] - self.min[[axes]])/(self.max[[axes]]-self.min[[axes]])
        else:
            X = (X - self.min)/(self.max-self.min)

        bounds = np.array(list(itertools.repeat([0,1], len(X))))

        return X, bounds
    
    def grid_search(self, X = None, axes = None, actuate = None, cost = None,
                    plot = False, steps = 10):
        ''' An N-dimensional grid search routine '''
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
        best_acquisition_value = 999

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
        ''' Watch for function recieveing a 2d x with higher dimensional state vectors (disagreement with internal GP dimension) '''
        mu, sigma = gp.predict(np.atleast_2d(x), return_std = True)
        return (b*mu+np.sqrt(1-b**2)*sigma)

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
        X, bounds = self.initialize_optimizer(axes)

        N = len(X)
        c = np.array([cost(X, axes=axes)])

        points, costs = self.random_sampling(cost, 15, bounds, axes=axes)
        X = np.append(np.atleast_2d(X), points, axis=0)
        c = np.append(c, costs)
        kernel = C(1.0, (1e-3, 1e3)) * RBF(10, (1e-2, 1e2))
        self.gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10)
        for i in range(iterations):
            self.gp.fit(X,c)
            b = 1
            #b = np.cos(2*np.pi*i/(iterations-1))
            X_new = self.gaussian_process_next_sample(X, bounds, b, self.effective_cost, self.gp, greater_is_better=False, restarts=10)
            X_new = np.atleast_2d(X_new)
            X = np.append(X, X_new, axis=0)
            c = np.append(c, self.cost(X[-1], axes = axes))
        self.actuate(self.unnormalize(X[np.argmin(c)], axes), axes)
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

    def random_sampling(self, cost, N, bounds, axes=None):
        ''' Performs a random sampling of the cost function at N points within the specified bounds '''
        points = np.random.uniform(size=(N,bounds.shape[0]))
        c = []
        for point in points:
            c.append(cost(point,axes=axes))

        return points, c

    def skl_minimize(self, cost, method = 'L-BFGS-B', X = None, axes = None):
        X, bounds = self.initialize_optimizer(axes)
        res = minimize(fun=cost,
                   x0=X,
                   bounds=bounds,
                   method=method,
                   args=(axes))
        #simplex for SKL is res = minimize(fun = cost,x0 = X.reshape(1, -1), method = 'Nelder-Mead', tol = 1e7)
        print("SKL:" + method + "=%s" % res)

    #possible to make a dictionary for these optimization methods and all possibile SKL optimize.minimze routines
    def optimize(self, routines = ['gp'], X = None, axes = None, iterations = 20, plot = True,
                 actuate = None, cost = None, span = 1, steps = 100, dither = 0.1, eta = 1, method = 'L-BFGS-B'):
        for r in routines:
            X = np.random.uniform(0, 1, size=(1,self.dim)) #change when axes is implemented
            if r == 'gp' or routines == ['all']:
                X, cost, points, c_pred = self.gaussian_process(X, axes, iterations = iterations, plot = plot,
                                                                span = span, steps = steps)
                print("Gau$$ian Proce$$ing=%s" % cost[-1])
            if r == 'sklm' or routines == ['all']:
                self.skl_minimize(cost = cost, method = method)
            if r == 'gs' and routines == ['all']:
                c = self.grid_search(plot = plot)
                print("Grid Search=%s" % c[-1])

    ''' Dimensionality Analytics and Reduction Algorithms '''
    def extract_pcs(self, X = None):
        #Method to use numpy's svd() function to obtain the principal components of the training set
        if X is None:
            X = self.state
        #take step to recenter data around the origin as necessary
        X_centered = X - X.mean(axis = 0) #NOTE: assumes that the dataset is centered around the origin
        U, s, Vt = np.linalg.svd(X_centered)
        #use the following to extract each pca given their index: c1 = Vt.T[:,0] where 0 is the index
        return Vt
        
    def pca_reduction(self, X = None, pvariance = 0.95):
        #Method to employ SKL's PCA to reduce dimensionality of the dataset based on a preserved variance threshold
        if X is None:
            X = self.state 
        
        #first determine the number of dimensions required to preserve variance threshold
        pca = PCA()
        pca.fit(X.copy) 
        d = np.argmax(np.cumsum(pca.explained_variance_ratio_) >= pvariance) + 1
        
        #now reduce the data set and find the breakdown of variance for each axis in the dataset
        pca = PCA(n_components = pvariance) #define either as a number of components or percentage of varaiance to preserve (e.g. pvariance = 3 or 0.95)
        X_reduced = pca.fit_tranform(X)
        variance_breakdown = pca.explained_variance_ratio_
        
        return X_reduced, variance_breakdown, d
    
    def pca_incremental(self, X = None, n_comps = 4, n_batches = 20):
        #Method to incrementally perform PCA on mini-batches of a dataset to split up the training data
        if X is None:
            X = self.state 
        
        inc_pca = IncrementalPCA(n_components = n_comps)
        for X_batch in np.array_split(X, n_batches):
            inc_pca.partial_fit(X_batch)
        X_reduced = inc_pca.transform(X)
        return X_reduced
        
    def pca_randomized(self, X = None, n_comps = 4):
        #Method employing PCA as a stochastic algorithm that efficiently finds approximations of the first d components
        if X is None:
            X = self.state
            
        rnd_pca = PCA(n_components = n_comps, svd_solver = "randomized") #svd_solver can be ‘auto’, ‘full’, ‘arpack’, or ‘randomized’
        X_reduced = rnd_pca.fit_transform(X)
        return X_reduced
    
    def pca_kernal(self, X = None, n_comps = 4, krnl = "rbf", gma = 0.04):
        #Method to employ kernal techniques to PCA, allowing complex nonlinear projections for dimensionality reduction
        if X is None:
            X = self.state
        
        rbf_pca = KernalPCA(n_components = n_comps, kernal = krnl, gamma = gma)
        X_reduced = rbf_pca.fit_transform(X)
        return X_reduced
        

if __name__ == '__main__':
    X0 = .2
    SNR = 100
    a = Optimizer(noise = 1/SNR)
    a.dim = 4
    pos = np.random.uniform(0, 1, size=(1, a.dim)) #np.ones(dim)*X0
    a.actuate(pos)

    #plt.title(r'Function optimization from %f, d=%i, SNR=%i'%(X0,a.dim, SNR))

    print('Optimization Results')
    a.optimize(routines = ['gs'])
