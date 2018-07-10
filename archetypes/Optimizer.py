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
<<<<<<< HEAD
        - take a state vecotr, decompose it into substates, run optimizations in series of separate substates
=======
        - take a state vector, decompose it into substates, run optimizations in series of separate substates
>>>>>>> 8f82d2e63fcd3d7c35c9c5b246b7bb9f6a9f4aa4
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
<<<<<<< HEAD
        self.position = np.array([])
        self.zero = np.array([])
        self.dim = len(self.position)
        self.mu = np.array([]) # gp routine best value
        self.sigma = np.array([]) # gp routine uncertainty
        self.cost_history = np.array([]) # any optimization routine cost history
        self.noise = 0
        self.plot = plt.figure() # figure for all optimization routine graphing

    ''' Base functions '''
    def actuate(self, point):
        self.position = point

    def cost(self, X = None):
=======
        self.plot = plt.figure() # figure for all optimization routine graphing
        self.noise = 0

    ''' Base functions '''
    def actuate(self, point):
        self.state = point

    def cost(self, X = None, axes = None):
>>>>>>> 8f82d2e63fcd3d7c35c9c5b246b7bb9f6a9f4aa4
        ''' A gaussian cost function in N dimensions. Overload in child classes with appropriate function '''
        self.actuate(self.unnormalize(X, axes), axes)
        X = np.atleast_2d(X)

        cost = 1
        sigma = 1/3
<<<<<<< HEAD

        full_cost = True

        if X is None:
            X = [self.position]
            full_cost = False
        point = np.array(X)
        point = np.atleast_2d(point)
        for n in range(point.shape[1]):
            cost *= np.exp(-point[:,n]**2/(2*sigma**2))
#        for n in range(point.shape[1]):
#            cost *= 2*np.exp(-(point[:,n]-1)**2/(2*sigma**2/4))
#        cost *= (1+np.random.normal(0,self.noise))
=======
        for n in range(X.shape[1]):
            cost *= np.exp(-X[:,n]**2/(2*sigma**2))
>>>>>>> 8f82d2e63fcd3d7c35c9c5b246b7bb9f6a9f4aa4
        cost += np.random.normal(0,self.noise)
        
        self.cost_history = np.append(self.cost_history, cost[0])

        return -cost

    ''' Optimization Routines and Algorithms '''
    def unnormalize(self, state, axes = None):
        if axes == None:
            return self.min + state * (self.max - self.min)
        else:
<<<<<<< HEAD
            return cost[-1]

    def measure(self, point, actuate, cost, delay = 0):
        actuate(point)
        time.sleep(delay)
        return cost()

    ''' Optimization Routines and Algorithms '''
    def prepare_substate(self, state, param_axes = None):
        if param_axes == None:
            return state
        return np.array(state[[param_axes]])
    
    def initialize_optimizer(self, X = None, actutate = None, cost = None):
        if X.all() == None:
            X = self.position
        if actutate == None:
            actuate = self.actuate
        if cost == None:
            cost = self.cost
        return X, actuate, cost

    def grid_search(self, X = None, param_axes = [0,1], actuate = None, cost = None,
                    plot = False, span = 1, steps = 10):
        ''' An N-dimensional grid search routine '''
        X, actuate, cost = self.initialize_optimizer(X, actuate, cost)
        X = self.prepare_substate(X, param_axes)
        
        ''' Generate search grid '''
        N = X.shape[1]
        grid = []
        for n in range(N):
            space = np.linspace(X[-1][n]-span/2, X[-1][n]+span/2, steps) #np.linspace(position[n]-span/2, position[n]+span/2, steps)
=======
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
>>>>>>> 8f82d2e63fcd3d7c35c9c5b246b7bb9f6a9f4aa4
            grid.append(space)
        grid = np.array(grid)
        points = np.transpose(np.meshgrid(*[grid[n] for n in range(N)])).reshape(-1,N)

        ''' Actuate search '''
        costs = []
        for point in points:
            costs.append(cost(point, axes))

        ''' Plot result if desired '''
        if plot:
<<<<<<< HEAD
            if len(X) == 2 and param_axes == None:
                ordinate_index = 0
                abscissa_index = 1
            else:
                ordinate_index = param_axes[0]
                abscissa_index = param_axes[1]
=======
            if len(X) == 2 and axes == None:
                ordinate_index = 0
                abscissa_index = 1
            else:
                ordinate_index = axes[0]
                abscissa_index = axes[1]
>>>>>>> 8f82d2e63fcd3d7c35c9c5b246b7bb9f6a9f4aa4
            ordinate_mesh, abscissa_mesh = np.meshgrid(points[:,ordinate_index], points[:, abscissa_index])
            cost_grid = griddata(points[:,[ordinate_index, abscissa_index]], cost, (ordinate_mesh,abscissa_mesh))
            plot = plt.pcolormesh(ordinate_mesh, abscissa_mesh, cost_grid, cmap='gist_rainbow')
            plt.colorbar(plot)
<<<<<<< HEAD
        guess = [1, self.position[0], self.position[1], 1, 1]
        fit = curve_fit(self.gaussian, points, cost, p0 = guess)[0]
        A, x0, y0, sigma_x, sigma_y = fit
        self.actuate([x0,y0])

        return points, cost, fit

    def gradient_calculate(self, X, d):
        ''' Compute the gradient and second-derivative (neglecting off-diagonal Hessian components) '''
        gradient = []
        hessian = []
        for i in range(len(X)):
            vec = np.zeros(len(X))
            vec[i] = d/2

            c0 = self.cost()

            self.actuate(X + vec)
            cp = self.cost()

            self.actuate(X-2*vec)
            cm = self.cost()

            gradient.append((cp-cm) / d)
            hessian.append((cp-2*c0+cm)/d**2)

            self.actuate(X + vec)
        return np.array(gradient), np.array(hessian)
    
    def gradient_descent(self, X = None, param_axes = None, actuate = None, cost = None, 
                         iterations = 30, plot = False, d = 0.1, eta = 1, threshold = 0.01):
        ''' A gradient descent minimization routine '''
        X, actuate, cost = self.initialize_optimizer(X, actuate, cost)
        X = self.prepare_substate(X, param_axes) 
        
        cost_history = [self.cost()]
        pos_history = [X]

        for i in range(iterations):
            g, h = self.gradient_calculate(X, d)
            self.actuate(X - eta*g)
            cost_history.append(self.cost()) #dimensional error with cost as self.dim long instead of 1
            pos_history.append(X)

        if plot:
            self.plot_optimization(func = cost_history, lbl = 'Gradient Descent')

        return pos_history, cost_history

    def simplex_initial(self, sampleRange, X = None):
        # generate self.dim+1 test points near current location
        if X is None:
            X = self.position
        points = np.zeros([self.dim+1, self.dim])
        for i in range(self.dim+1):
            points[i] = np.array(X)+np.random.uniform(low = -sampleRange/2, high = sampleRange/2, size=self.dim)
        return points

    def simplex_next(self, simplex, alpha = 1, gamma = 2, rho = 0.5, sigma = 0.5, actuate = None, cost = None):
        measures = np.zeros(self.dim+1)
        for i in range(len(simplex)):
            measures[i] = self.measure(simplex[i], actuate = actuate, cost = cost)

        sortIndex = np.argsort(measures)
        sortedMeasures = measures[sortIndex]
        sortedSimplex = simplex[sortIndex]
        newSimplex = sortedSimplex

        # calculate centroid of best dim points
        bestPoints = sortedSimplex[1::]
        bestMeasure = sortedMeasures[-1]
        worstPoint = sortedSimplex[0]
        bestPoint = sortedSimplex[-1]

        centroid = np.sum(bestPoints, axis = 0)/(self.dim)

        reflection = centroid + alpha * (centroid - worstPoint)
        reflectionValue = self.measure(reflection, actuate = actuate, cost = cost)

        if sortedMeasures[1] < reflectionValue < sortedMeasures[-1]:
            newSimplex[0] = reflection
        if reflectionValue > sortedMeasures[-1]:
            expansion = centroid + gamma*(reflection - centroid)
            expansionValue = self.measure(expansion, actuate = actuate, cost = cost)

            if expansionValue > sortedMeasures[-1]:
                newSimplex[0] = expansion
            else:
                newSimplex[0] = reflection
        elif reflectionValue < sortedMeasures[1]:
            if reflectionValue > sortedMeasures[0]:
                betterPoint = reflection
                betterValue = reflectionValue
            else:
                betterPoint = sortedSimplex[0]
                betterValue = sortedMeasures[0]
            contraction = rho*betterPoint +(1-rho)*centroid

            if self.measure(contraction, actuate = actuate, cost = cost) > betterValue:
                newSimplex[0] = contraction
            else:
                for i in range(self.dim):
                    newSimplex[i] = sigma*newSimplex[i]+(1-sigma)*bestPoint

        centroid = np.sum(newSimplex, axis = 0)/(self.dim)
        centroidCost = self.measure(centroid, actuate = actuate, cost = cost)

        return newSimplex, bestMeasure, centroidCost

    def rjf_simplex(self, X = None, param_axes = None, actuate = None, cost = None,
                    iterations = 30, plot = False, sampleRange = 0.5): 
        ''' A simplex minimization algorithm brought to you by the one and only Robbie Fasano '''
        X, actuate, cost = self.initialize_optimizer(X, actuate, cost)
        X = self.prepare_substate(X, param_axes) 
        
        simplex = self.simplex_initial(sampleRange, X = X)
        simplex, bestMeasure, centroidCost = self.simplex_next(simplex, actuate = actuate, cost = cost)

        cost_history = []
        pos_history = []

        for i in range(iterations):
            simplex, bestMeasure, centroidCost = self.simplex_next(simplex, actuate = actuate, cost = cost)
            cost_history.append(bestMeasure)
            pos_history.append(simplex)
        '''
        sampleReduction = 0.5
        for restart in range(restarts):
            sampleRange *= sampleReduction
            simplex = self.firstSimplex(sampleRange)
            simplex, bestMeasure = self.nextSimplex(simplex)
            for iteration in range(iterations-1):
                simplex, bestMeasure = self.nextSimplex(simplex)
                #print('Simplex restart %i, iteration %i; best = %f V'%(restart+1,iteration+1, bestMeasure))
                '''
        if plot:
            self.plot_optimization(func = cost_history, lbl = 'RJF Simplex')

        return pos_history, cost_history

    def skl_simplex(self, X = None, param_axes = None, actuate = None, cost = None,
                    iterations = 30, plot = False, tolerance = 1e7):
        ''' A simplex minimization algorithm brought to you by the generic Scikit-Learn Library'''
        X, actuate, cost = self.initialize_optimizer(X, actuate, cost)
        X = self.prepare_substate(X, param_axes) 
        
        self.cost_history = np.array([]) #use universal cost history since Scikit uses cost internally
        best_x = None
        best_acquisition_value = 1
        bounds = np.array(list(itertools.repeat([0,1], len(X)))) #for normalized parameters, go from -1,1
        n_params = len(X)

        for X in np.random.uniform(bounds[0][0], bounds[0][1], size=(iterations, n_params)):
            res = minimize(fun = cost,x0 = X.reshape(1, -1), method = 'Nelder-Mead', tol = tolerance)
            if res.fun < best_acquisition_value:        #
                best_acquisition_value = res.fun
                best_x = res.x

        if plot:
            self.plot_optimization(func = self.cost_history, lbl = 'Scikit-Learn Simplex')

        return best_x

    def gaussian_process_next_sample(self, X, b, acquisition_func, gaussian_process, 
                                     evaluated_loss, greater_is_better=False, restarts=25):
        n_params = X.shape[0]
        bounds = np.array(list(itertools.repeat([0,1], n_params))) #for normalized parameters, go from -1,1
        best_x = None
        best_acquisition_value = 1

        for starting_point in np.random.uniform(bounds[0][0], bounds[0][1], size=(restarts, n_params)):
=======

        best_point = points[np.argmin(costs)]
        self.actuate(self.unnormalize(best_point, axes), axes)

        return points, costs

    def gaussian_process_next_sample(self, X, bounds, b, acquisition_func, gaussian_process,
                                     greater_is_better=False, restarts=25):
        best_x = None
        best_acquisition_value = 1

        for starting_point in np.random.uniform(bounds[0][0], bounds[0][1], size=(restarts, X.shape[1])):
>>>>>>> 8f82d2e63fcd3d7c35c9c5b246b7bb9f6a9f4aa4
            res = minimize(fun=acquisition_func,
                       x0=starting_point.reshape(1, -1),
                       bounds=bounds,
                       method='L-BFGS-B',
<<<<<<< HEAD
                       args=(b, gaussian_process)) #possibly args=(gaussian_process, evaluated_loss, greater_is_better, n_params))
=======
                       args=(b, gaussian_process))
>>>>>>> 8f82d2e63fcd3d7c35c9c5b246b7bb9f6a9f4aa4
            if res.fun < best_acquisition_value:
                best_acquisition_value = res.fun
                best_x = res.x

<<<<<<< HEAD
            #THRESHOLD TO ENABLE AFTER LOTS OF EXPERIMENTATION
            #if len(self.sigma) > 100 and np.std(self.sigma[-1:-100]) < 0.003:
            #if len(self.mu) > 100 and np.std(self.mu[-1:-100]) < 0.003:
                #return best_x
        return best_x

    def effective_cost(self, x, b, gp):
        print(x)
        print(x.reshape(-1,1))
        print(x.reshape(1,-1))
        mu, sigma = gp.predict(x.reshape(-1,1), return_std = True)
        return -(b*mu+np.sqrt(1-b**2)*sigma)

    def expected_improvement(self, x, gp, evaluated_loss, greater_is_better=True, n_params=1):
        x_to_predict = x.reshape(-1, len(self.position))

        mu, sigma = gp.predict(x_to_predict, return_std=True)
        self.mu = np.append(self.mu, mu[0])
        self.sigma = np.append(self.sigma, sigma[0])

        if greater_is_better:
            loss_optimum = np.max(evaluated_loss)
        else:
            loss_optimum = np.min(evaluated_loss)
        scaling_factor = (-1) ** (not greater_is_better)

        # In case sigma equals zero
        with np.errstate(divide='ignore'):
            Z = scaling_factor * (mu - loss_optimum) / sigma
            expected_improvement = scaling_factor * (mu - loss_optimum) * norm.cdf(Z) + sigma * norm.pdf(Z)
            expected_improvement[sigma == 0.0] == 0.0

        return -1 * mu #maximize the value
#        return -1 * expected_improvement #maximize learning about model
        
    def gaussian_process(self, X = None, param_axes = None, actuate = None, cost = None,
                    iterations = 10, plot = False, span = 10, steps = 100, random_search = False):    
        ''' Guassian Processing from https://github.com/thuijskens/bayesian-optimization/blob/master/python/gp.py
            and https://www.nature.com/articles/srep25890.pdf '''
        X, actuate, cost = self.initialize_optimizer(X, actuate, cost)
        X = self.prepare_substate(X, param_axes) 
        
        N = X.shape[1]
        c = np.array([self.cost(X)])
        kernel = C(1.0, (1e-3, 1e3)) * RBF(10, (1e-2, 1e2))
        self.gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10)

        initial_step = -0.05
        X_new = X + initial_step
        for i in range(iterations):
            X = np.atleast_2d(np.append(X, X_new)).T
            print('X')
            print(X)
=======
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
>>>>>>> 8f82d2e63fcd3d7c35c9c5b246b7bb9f6a9f4aa4
            X = X.reshape(-1,N)
            c = np.append(c, self.cost(X[-1], axes = axes))

            self.gp.fit(X,c)
<<<<<<< HEAD
            # do grid search on prediction OR scipy.optimize's minimize to select next sample
            if random_search:
                grid = []
                for n in range(N):
                    grid.append(np.linspace(X[-1][n]-span/2, X[-1][n]+span/2, steps))
                grid = np.array(grid)
                points = np.transpose(np.meshgrid(*[grid[n] for n in range(N)])).reshape(-1,N)
                c_pred, sigma = self.gp.predict(points, return_std = True)
                b = 0.5
                effective_cost = b*c_pred + (1-b)*sigma
                X_new = points[np.argmax(effective_cost)]
            else:
                points = []
                c_pred = []
                b = np.cos(2*np.pi*i/(iterations-1))
                X_new = self.gaussian_process_next_sample(X, b, self.effective_cost, self.gp, c, greater_is_better=True, restarts=10)

        if plot:
            self.plot_optimization(func = c, lbl = 'Gaussian Processing')
=======

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
>>>>>>> 8f82d2e63fcd3d7c35c9c5b246b7bb9f6a9f4aa4

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

    def plot_optimization(self, func, lbl = None, yscl = 'log',
                          ylbl = 'Optimization Function', xlbl = 'Iteration #'):
            plt.plot(func, label = lbl)
            plt.yscale(yscl)
            plt.ylabel(ylbl)
            plt.xlabel(xlbl)
            plt.legend()

    def optimize(self, routines = ['gp'], X = None, param_axes = None, iterations = 20, plot = True,
                 actuate = None, cost = None, span = 1, steps = 100, dither = 0.1, eta = 1):
#        if param_axes == None:   #set the indices that the user would like to specify for each optimization routine
#            param_axes = [0, self.dim]

        for r in routines:
            X = np.random.uniform(0, 1, size=(1,self.dim)) #change when param_axes is implemented
            self.cost_history = np.array([])
            if r == 'gp' or routines == ['all']:
                X, cost, points, c_pred = self.gaussian_process(X, param_axes, iterations = iterations, plot = plot,
                                                                span = span, steps = steps)
                print("Gau$$ian Proce$$ing=%s" % cost[-1]) 
                '''unstable as of now - able to take a set of param_axes isolated from position
                standardized all parameter orders and names across all optimization functions
                isolated local variables to X instead of self.position such that actuations can be unique to methods
                plot optimization general method
                optimize general method for iterative series optimization or flexible ensemble optimization routines
                POSSIBLE TO ADD a dictionary for these optimization methods and all possible scikit-learn optimize.minimize routines
                '''
            if r == 'skl_splx' or routines == ['all']:
                X2 = self.skl_simplex(X, param_axes, iterations = iterations, plot=plot)
                print("Scikit-Learn Simplex=%s" % X2[0])
            if r == 'rf_splx' or routines == ['all']:
                h, c = self.rjf_simplex(X, param_axes, iterations = iterations, plot = plot)
                print("RJF Simplex=%s" % c[-1])
            if r == 'gd' or routines == ['all']:
                h, c = self.gradient_descent(X, param_axes, iterations = iterations, plot = plot, d = dither, eta = 1)
                print("Gradient Descent=%s" % c[-1][-1])
            if r == 'gs':  #WARNING - plotting grid search does not work
                c = self.grid_search(X, param_axes = [0,1] ,plot = plot,  span = span, steps = steps, axes = [0,1], )
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
<<<<<<< HEAD
    a.optimize(routines = ['all'])
=======
    a.optimize(routines = ['all'])
>>>>>>> 8f82d2e63fcd3d7c35c9c5b246b7bb9f6a9f4aa4
