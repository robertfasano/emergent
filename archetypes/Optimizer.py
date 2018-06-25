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
        - First implement GP optimization in Aligner
'''
import numpy as np
import sys
import os
import time
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
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
        self.position = np.array([])
        self.zero = np.array([])
        self.dim = len(self.position)
        self.mode = []
        self.noise = 0
    ''' Base functions '''
    def actuate(self, point):
        self.position = point
    
    def cost(self, X = None):
        ''' A gaussian cost function in N dimensions. Overload in child classes with appropriate function '''
        cost = 1
        sigma = 1
        
        full_cost = True
        
        if X is None:
            X = [self.position]
            full_cost = False
        point = np.array(X)
        for n in range(point.shape[1]):
            cost *= np.exp(-point[:,n]**2/(2*sigma**2))
        cost *= (1+np.random.normal(0,self.noise))
        
        if full_cost:
            return cost
        else:
            return cost[-1]
    
    def measure(self, point, delay = 0):
        self.actuate(point)
        time.sleep(delay) 
        return self.cost()

    ''' Algorithms '''
    
    def gradient_calculate(self, d):
        ''' Compute the gradient and second-derivative (neglecting off-diagonal Hessian components) '''
        gradient = []
        hessian = []
        for i in range(len(self.position)):
            vec = np.zeros(len(self.position))
            vec[i] = d/2
            
            c0 = self.cost()
        
            self.actuate(self.position + vec)
            cp = self.cost()
            
            self.actuate(self.position-2*vec)
            cm = self.cost()
            
            gradient.append((cp-cm) / d)
            hessian.append((cp-2*c0+cm)/d**2)
            
            self.actuate(self.position + vec)
        return np.array(gradient), np.array(hessian)
        
    
    def gradient_descent(self, d, eta=1, iterations = 30, threshold = 0.01, plot = False):
        initial = time.time()
        cost = [self.cost()]
        history = [self.position]
        
        for i in range(iterations):
            g, h = self.gradient_calculate(d)
            
            self.actuate(self.position + eta*g)
            cost.append(self.cost())
            history.append(self.position)
            
        if plot:
            plt.plot(cost, label = 'Gradient descent')
            plt.xlabel('Iteration #')
            plt.ylabel('Optimization function')
            plt.legend()
        print(time.time() - initial)
        return cost, history
    
    def grid_search(self, span, steps, axes = None, plot = False):
        ''' An N-dimensional grid search routine '''
        position = self.position
        if axes != None:
            position = np.array(position)[axes]
            
        ''' Generate search grid '''
        N = len(position)
        grid = []
        for n in range(N):
            space = np.linspace(position[n]-span/2, position[n]+span/2, steps)
            grid.append(space)
        grid = np.array(grid)
        points = np.transpose(np.meshgrid(*[grid[n] for n in range(N)])).reshape(-1,N)
        
        ''' Actuate search '''
        cost = []
        for point in points:
            self.actuate(point)
            cost.append(self.cost())

        ''' Plot result if desired '''
        if plot:
            if len(position) == 2 and axes == None:
                ordinate_index = 0
                abscissa_index = 1
            elif len(position) == 2:
                ordinate_index = axes[0]
                abscissa_index = axes[1]
            ordinate_mesh, abscissa_mesh = np.meshgrid(points[:,ordinate_index], points[:, abscissa_index])
            cost_grid = griddata(points[:,[ordinate_index, abscissa_index]], cost, (ordinate_mesh,abscissa_mesh))
            plot = plt.pcolormesh(ordinate_mesh, abscissa_mesh, cost_grid, cmap='gist_rainbow')
            plt.colorbar(plot)
        guess = [1, self.position[0], self.position[1], 1, 1]
        fit = curve_fit(self.gaussian, points, cost, p0 = guess)[0]
        A, x0, y0, sigma_x, sigma_y = fit
        self.actuate([x0,y0])

        return points, cost, fit
    
    
    def simplex_initial(self, sampleRange): 
        # generate self.dim+1 test points near current location
        points = []
        self.dim = len(self.position)
        points = np.zeros([self.dim+1, self.dim])
        for i in range(self.dim+1):
            points[i] = np.array(self.position)+np.random.uniform(low = -sampleRange/2, high = sampleRange/2, size=self.dim)
        return points
    
    def simplex_next(self, simplex, alpha = 1, gamma = 2, rho = 0.5, sigma = 0.5):
        measures = np.zeros(self.dim+1)
        for i in range(len(simplex)):
            measures[i] = self.measure(simplex[i])

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
        reflectionValue = self.measure(reflection)

        if sortedMeasures[1] < reflectionValue < sortedMeasures[-1]:
            newSimplex[0] = reflection
        if reflectionValue > sortedMeasures[-1]:
            expansion = centroid + gamma*(reflection - centroid)
            expansionValue = self.measure(expansion)

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

            if self.measure(contraction) > betterValue:             
                newSimplex[0] = contraction
            else:
                for i in range(self.dim):
                    newSimplex[i] = sigma*newSimplex[i]+(1-sigma)*bestPoint
     
        centroid = np.sum(newSimplex, axis = 0)/(self.dim)
        centroidCost = self.measure(centroid)
        
        return newSimplex, bestMeasure, centroidCost
    
    def simplex(self, iterations = 30, plot = False):
        initial = time.time()
        #restarts = 5
        sampleRange = 0.5

        simplex = self.simplex_initial(sampleRange)
        simplex, bestMeasure, centroidCost = self.simplex_next(simplex)
        
        cost = []
        history = []

        for i in range(iterations):
            simplex, bestMeasure, centroidCost = self.simplex_next(simplex)
            cost.append(bestMeasure)
            history.append(simplex)
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
            plt.plot(cost, label = 'Simplex')
            plt.yscale('log')
            plt.ylabel('Optimization function')
            plt.xlabel('Iteration #')
            plt.legend()
            
        return time.time() - initial #return elapsed time for simplex to run  
             
    def gaussian_process(self, iterations = 5, initial_step = .5, span = 10, steps = 100, plot = False):
        X = np.array([self.position])
        N = X.shape[1]
        c = np.array([self.cost(X)])
        
        kernel = C(1.0, (1e-3, 1e3)) * RBF(10, (1e-2, 1e2))
        gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10)
        x_pred = np.atleast_2d(np.linspace(0, 10, 1000)).T
        x_pred, x_pred = np.meshgrid(x_pred, x_pred)
        
        X_new = X + initial_step
        
        for i in range(iterations):
            X = np.atleast_2d(np.append(X, X_new)).T
            X = X.reshape(-1,N)
            c = self.cost(X)
            gp.fit(X,c)
            
            # do grid search on prediction
            N = X.shape[1]
            grid = []
            for n in range(N):
                space = np.linspace(X[-1][n]-span/2, X[-1][n]+span/2, steps)
                grid.append(space)
            grid = np.array(grid)
            points = np.transpose(np.meshgrid(*[grid[n] for n in range(N)])).reshape(-1,N)
            
            c_pred, sigma = gp.predict(points, return_std = True)
            
            b = 1
            effective_cost = b*c_pred + (1-b)*sigma
            X_new = points[np.argmax(effective_cost)]
            
        if plot:
            plt.plot(c, label = 'Gaussian process')
            plt.yscale('log')
            plt.ylabel('Optimization function')
            plt.xlabel('Iteration #')
            plt.legend()

        return X, c, points, c_pred

if __name__ == '__main__':
    a = Optimizer()
    d = 3
    sigma = 5
    SNR = 10
    a.noise = 1/SNR
    pos = np.ones(d)*sigma
    iterations = 30


    a.position = pos
    a.dim = len(a.position)

    X, cost, points, c_pred = a.gaussian_process(iterations = iterations, span = 1, steps = 30, initial_step = -.5, plot = True)

    a.position = pos
#    c, h = a.gradient_descent(d=.1, eta=1, plot = True, iterations = iterations)
    
    a.position = pos
    t = a.simplex(plot = True, iterations = iterations)
    
#    plt.yscale('linear')
    plt.title(r'Gaussian function optimization from %i$\sigma$, d=%i, SNR=%i'%(sigma,d, SNR))
#    c = a.explore(5,30, axes = [0,1], plot = True)

    