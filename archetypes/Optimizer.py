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
import json
import time
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-2]))

class Aligner():
    def __init__(self, filename):
        self.filename = filename
        self.position = np.array([])
        self.zero = np.array([])
        self.dim = len(self.position)
        self.mode = []
        
    def load_position(self):
        ''' Recalls the last saved position to ensure that alignment is persistent
            across device restarts '''
        with open(self.filename, 'r') as file:
            self.parameters = json.load(file)
        self.position = self.parameters['position']
        
    def actuate(self, point):
        self.position = point
        
        
    def explore(self, span, steps, axes = None, plot = False):
        ''' An N-dimensional grid search routine '''
        initial = time.time()
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
#        A,x0,y0,sigma_x,sigma_y = curve_fit(self.gaussian, points, cost)[0]
#        print(A,x0,y0,sigma_x,sigma_y)
#        self.actuate([x0,y0])
#        self.mode.append(sigma_x)
#        print(time.time()-initial)
#        best_point = points[np.argmax(cost)]
#        self.actuate(best_point)
        return points, cost, fit

    def gaussian(self, X, A, x0, y0, sigma_x, sigma_y):
        x = X[:,0]
        y = X[:,1]
        return A*np.exp(-(x-x0)**2/sigma_x**2)*np.exp(-(y-y0)**2/sigma_y**2)
        
    # then study the size of the mode
        #through trig move the mirror back and see how ideal step size and range change
        #calibrate it from how big the fiber mode is in terms of distance from the fiber angle
        #measure how big it is - the characteristic size of the gaussian peak, use that as voltage units, converted to angle later
        #look at cost threshhold to stop fitting after a certain point (above ~.1)
       #prepare gradient descent with given eta to approach the peak of cost
       #make a gradient descent function for eta, get there in the fewest steps, calls first one with varying eta (start at 1)
       #compute the derivative of the number of steps with respect to eta - gradient descent on that to optimize eta
       #visualize the motion, so plot the trajectories (plot in white during the gradient descent, save all points in the sample (plt.scatter))
       #or single axes with x and y components to find different gains for both axes
       #compute gradient
       #could learn both what dither and eta is, use gain and max eta as parameters for limits
       
    def measure(self, point):
        self.actuate(point)
        time.sleep(0.01) #in case a delay is needed
        return self.cost()
    
    def firstSimplex(self, sampleRange): 
        # generate self.dim+1 test points near current location
        points = []
        self.dim = len(self.position)
        points = np.zeros([self.dim+1, self.dim])
        for i in range(self.dim+1):
            points[i] = np.array(self.position)+np.random.uniform(low = -sampleRange/2, high = sampleRange/2, size=self.dim)
        return points
    
    def nextSimplex(self, simplex, alpha = 1, gamma = 2, rho = 0.5, sigma = 0.5):
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
    
    def run_simplex(self):
        print('Starting simplex routine.')
        initial = time.time()
        maxIterations = 30
        #restarts = 5
        sampleRange = 0.5

        simplex = self.firstSimplex(sampleRange)
        simplex, bestMeasure, centroidCost = self.nextSimplex(simplex)
        
        runCount = 0
        previousCentroidCost = 0
        cost = []
        history = []
        #for iteration in range(iterations-1):
        #until reaches gain difference at centroid (np.abs(centroidCost - previousCentroidCost) / centroidCost > 0.0001)
        #or reaches certain percentage of the past volume of the simplex
        for i in range(maxIterations):
            previousCentroidCost = centroidCost
            simplex, bestMeasure, centroidCost = self.nextSimplex(simplex)
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
        plt.plot(np.array(cost)) 
        #x = np.array(history)[:,0]
        #y = np.array(history)[:,1]
        #plt.plot(x, y,'.')
        print(bestMeasure)
        return time.time() - initial #return elapsed time for simplex to run  
            
    def gradient(self, d):
        #yield n-dimensional gradient - optimize later to reuse previous costs
        gradient = []
        for i in range(len(self.position)):
            c2 = self.cost()
            vec = np.zeros(len(self.position))
            vec[i] = d
            self.actuate(self.position + vec)
            c1 = self.cost()
            self.actuate(self.position-vec)
            gradient.append((c1-c2) / d)
        return np.array(gradient)
        
    
    def optimize_gradient(self, d, eta=1, threshold = 0.01, plot = False):
        initial = time.time()
        cost = [self.cost()]
        while True:
            g = self.gradient(d)
            self.actuate(self.position + eta * g)

            cost.append(self.cost())
            if np.abs((cost[-1] - cost[-2]) / cost[-2]) < threshold:
                break
            
        if plot:
            plt.plot(cost)
            plt.xlabel('Iteration #')
            plt.ylabel('Optimization function')
        print(time.time() - initial)
        return cost
    
    def optimize_eta(self, min_eta = 1, max_eta = 25, steps = 25):
        costs = []
        etas = np.linspace(min_eta,max_eta,steps)
        for eta in etas:
            self.actuate([3,3])
            cost = self.optimize_cost(d=0.1, eta=eta)
            costs.append(cost)
        
        steps_to_converge = []
        etas_successful = []
        max_cost = np.array(cost).max()
        for i in range(len(costs)):
            if costs[i][-1] > 0.9*max_cost:
                steps_to_converge.append(len(costs[i]))
                etas_successful.append(etas[i])
        plt.plot(etas_successful, steps_to_converge)
        plt.xlabel('Gradient gain')
        plt.ylabel('Steps to converge')
            
    def test_optimization(self, cost, algorithm, params):
        # for many loops:
            # create random start point (with signal)
            # run optimization from random start point
            # return number of steps for convergence
        return

    def cost(self, noise=.02):
        ''' A gaussian cost function in N dimensions. Overload in child classes with appropriate function '''
        cost = 1
        sigma = 1
        point = self.position
        for n in range(len(point)):
            cost *= np.exp(-point[n]**2/(2*sigma**2))
        cost *= (1+np.random.normal(0,noise))
        return cost   
        
    def save_position(self):
        with open(self.filename, 'w') as file:
            file.write(str(self.position))
        
    def read_position(self):
        with open(self.filename, 'r') as file:
            pos = file.read(self.filename)
        pos = pos.split('[')[1].split(']')[0]
        self.position = []
        for coord in pos.split(','):
            self.position.append(float(coord))
            
if __name__ == '__main__':
    a = Aligner(None)
    a.position = np.array([0,0,5])
    a.dim = len(a.position)
    print(a.run_simplex())
    #c = a.explore(5,30, axes = [0,1], plot = True)

    