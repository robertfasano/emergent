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
import sklearn.cluster
from sklearn import metrics
import pandas as pd
import time
def warn(*args, **kwargs):
    pass
import warnings
warnings.warn = warn

class Optimizer():
    def __init__(self, control_node):
        ''' Initialize the optimizer and link to the parent Control node '''
        self.parent = control_node
        self.actuate = self.parent.actuate

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
    def unnormalize(self, norm):
        ''' Converts normalized (0-1) state to physical state based on specified
            max and min parameter values. '''
        unnorm = {}
        
        for i in norm.keys():
                min = self.parent.settings[i]['min']
                max = self.parent.settings[i]['max']
                unnorm[i] = min + norm[i] * (max-min)
        return unnorm
        
    def normalize(self, unnorm):
        ''' Normalizes a state or substate based on min/max values saved in the parent control node '''
        norm = {}
        for i in unnorm.keys():
                min = self.parent.settings[i]['min']
                max = self.parent.settings[i]['max']
                norm[i] = (unnorm[i] - min)/(max-min)
        return norm
                
        
    def initialize_optimizer(self, state):
        ''' Prepares a normalized substate and appropriate bounds. '''
        cols = list(state.keys()
        
        cols.append('cost')
        self.history = pd.DataFrame(index = [], columns = cols) #pd.Series(index=[])

        state = self.normalize(state)
        bounds = np.array(list(itertools.repeat([0,1], len(state.keys()))))

        return state, bounds

    def line_search(self, state, cost, step = 0.1):
        ''' Searches a single axis/dimension for a minimum using a moving derivative. Argument should be a state dict with one or more components; if more than one component is present, they are done sequentially.'''
        state, bounds = self.initialize_optimizer(state)

        for key in state.keys():
                X = {key, state[key]}        # extract single axis
                costs = [cost(X)]
                #first compute the gradient to check which direction to move
                init_step = 5 * step
                init_points = []

                X[key] -= init_step
                init_points.append(cost(X))

                for i in range(2):
                        X[key] += init_step
                init_points.append(self.cost(X))

                dir = -1*np.sign(np.mean(np.diff(init_points))) #determine direction from differences towards mininum

                if dir is -1: #undo move in wrction
                        X[key] -= init_step
                        self.actuate(X)

                #now, perform the line search
                num_points = 5 #for moving derivative and to keep track of historically
                lastNPoints = np.array([])
                movingDeriv = 0

                while True:
                        X[key] += dir*step
                        val = cost(X)
                        costs.append(val)
                        lastNPoints = np.append(lastNPoints, val)
                        if len(lastNPoints) > num_points:
                                lastNPoints = np.delete(lastNPoints,0)
                        if len(lastNPoints) > 1:
                                movingDeriv = np.mean(np.diff(lastNPoints))
                        if movingDeriv > 0 and len(lastNPoints) == num_points:
                                numSteps = len(lastNPoints) - np.argmin(lastNPoints) - 1
                                X[key] -= dir*step*numSteps
                                costs.append(self.cost(X))
                                break
                change = (costs[-1]-costs[0])/costs[0]*100
                char = {1: '+', -1: '-'}[np.sign(change)]
                print('Line search on axis %s terminated'%key)
                print('Initial cost: %f'%costs[0])
                print('Final cost: %f (%s%.1f%%)'%(costs[-1], char, change)
                                

    def grid_search(self, state, cost,
                    plot = False, loadExisting = False, steps = 10):
        ''' An N-dimensional grid search routine with optional plotting. '''
        state, bounds = self.initialize_optimizer(state)
        if loadExisting:
            costs = np.loadtxt('costs.txt')
            points = np.loadtxt('points.txt')
        else:    
            ''' Generate search grid '''
            N = len(state.keys)
            grid = []
            for n in range(N):
                space = np.linspace(bounds[n][0], bounds[n][1], steps)
                grid.append(space)
            grid = np.array(grid)
            points = np.transpose(np.meshgrid(*[grid[n] for n in range(N)])).reshape(-1,N)
        
            ''' Actuate search '''
            costs = []
            for point in points:
                target = {}
                for i in len(point):
                    target[state.keys()[i]] = point[i]
                costs.append(self.cost(target))
            
            np.savetxt('costs.txt', np.array(costs))
            np.savetxt('points.txt', np.array(points))
                
        ''' Plot result if desired '''
        ax = None
        if plot and len(state.keys()) is 2:
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

        best_point = points[np.argmin(costs)]
        self.actuate(self.unnormalize(best_point))

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

    def skl_minimize(self, cost, method = 'L-BFGS-B', X = None, axes = None, plot = False, tol = 1e-7):
        ''' Runs a specified scikit-learn minimization method on the target axes and cost. '''
        X, bounds = self.initialize_optimizer(axes)
        res = minimize(fun=cost,
                   x0=X,
                   bounds=bounds,
                   method=method,
                   args=(axes),
                   tol = tol)
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
        ''' Employs SKL's PCA to reduce dimensionality of the dataset based on a preserved variance threshold. '''
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
        ''' Employs kernel techniques to PCA, allowing complex nonlinear projections for dimensionality reduction. '''
        rbf_pca = KernelPCA(n_components = n_comps, kernel = krnl, gamma = gma)
        X_reduced = rbf_pca.fit_transform(X)
        return X_reduced
    
    #NOTE: NOT TESTED AS OF YET 7.20.18
    def cluster(self, name = 'k-means++', init = 'k-means++', n_clusters = 4, n_init = 10, 
                X = None, axes = None):
        ''' General Clustering from scikit-learn implementing various clustering techniques; 
        implementation aided by http://scikit-learn.org/stable/modules/clustering'''
        X, bounds = self.initialize_optimizer(X, axes)
        labels = None
        
        ''' K-Means - very large n_samples and medium n_clusters scalability (Use MiniBatch code)
         general-purose, even cluster size, flat geometry (distance between points), not too many clusters '''
        if name is 'k-means++': #could be k-mean++ or random init
                estimator = KMeans(init = init, n_clusters = n_clusters, n_init = n_init)
        if name is 'PCA-based': #PCA modified k-means++
            pca = PCA(n_components = n_clusters).fit(X)
            estimator = KMeans(init = pca.components_, n_clusters = n_clusters, n_init = 1) #n_init 1 b/c PCA is deterministic
        estimator.fit(X)
        ''' Affinity propagation - not scalable with n_samples, uses many clusters,
        uneven cluster sizes, non-flat geometry (graph distance - nearest neighbor graph), large computational complexity '''
        if name is 'af':
            # strange to test - must use sample data
            estimator = AffinityPropagation(preference=-50).fit(X)
            cluster_centers_indices = estimator.cluster_centers_indices_
            labels = estimator.labels_
            n_clusters_ = len(cluster_centers_indices) #estimated/determined n_clusters val
        
        ''' Mean-shift - not scalable with n_samples, uses many clusters, uneven cluster size,
        non-flat geometry (distance between points) '''
        if name is 'mean-shift':
            bandwidth = estimate_bandwidth(X, quantile=0.2, n_samples=len(X) ** 2)
            estimator = MeanShift(bandwidth=bandwidth, bin_seeding=True)
            estimator.fit(X)
            labels = estimator.labels_
            cluster_centers = estimator.cluster_centers_
            n_clusters_ = len(np.unique(labels))
        
        ''' DBSCAN - scalable with very large n_samples / medium n_clusters, uses of non-flat geometry,
        uneven cluster sizes, geometry of distances between nearest points - watch out for memory consumption'''
        if name is 'dbscan':
            estimator= DBSCAN(eps=0.3, min_samples=10).fit(X)
            core_samples_mask = np.zeros_like(estimator.labels_, dtype=bool)
            core_samples_mask[estimator.core_sample_indices_] = True
            labels = estimator.labels_
            n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
            
         #to be implemented if needed later on
        ''' Ward hierarchical clustering - scalable with large number of n_samples/n_clusters, uses
        many clusters with possible connectivitiy constraints, geometry of distance between points '''
        ''' Agglomerative clustering - scalable with large n_samples/n_clusters, uses of many clusters,
        possible connectivity constraints, non-Euclidean distances (any pairwise distances for geometry) '''
        ''' Birch - scalable with large n_clusters and n_samples, uses for large datasets, outlier removal,
        data reduction, and geometry of Euclidean distances between points '''
        ''' Gaussian mixtures - not scalable, uses flat geometry, good for density estimation,
        geometry of Mahalanobis(?) distances to centers '''
             
        return estimator, labels, n_clusters
        
    def bench_clustering(self, estimator, names = ['k-means++'], 
                         n_clusters = 4,n_init = 10, X = None, axes = None):
        ''' Method to benchmark and compare each clustering algorithm provided in scikit-learn '''
        n_samples = len(X) ** 2 #the number of points taken
        n_features = len(X)
        print("n_clusters: %d, \t n_samples %d, \t n_features %d"
              % (n_clusters, n_samples, n_features))
        print(82 * '_')
        print('init\t\ttime\tinertia\thomo\tcompl\tv-meas\tARI\tAMI\tsilhouette')
        for name in names:
            estimator, labels, n_clusters = self.cluster(init = name, n_clusters = n_clusters, n_init = n_init, X = X, axes = axes)
            print('%-9s\t%.2fs\t%i\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f'
          % (name, (time() - t0), estimator.inertia_,
             metrics.homogeneity_score(labels, estimator.labels_),
             metrics.completeness_score(labels, estimator.labels_),
             metrics.v_measure_score(labels, estimator.labels_),
             metrics.adjusted_rand_score(labels, estimator.labels_),
             metrics.adjusted_mutual_info_score(labels,  estimator.labels_))

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
