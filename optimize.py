import numpy as np
import matplotlib.pyplot as plt
import time


def line_search(x0, cost, actuate, step, threshold, full_output = False, test = False, gradient = False, min_step = None, failure_threshold = None):
    x = [x0]
    
    ''' Measure initial cost '''
    if test:
        c = [cost(x[-1])]
        sign = np.sign(c[-1])    # note a negative sign between the etalon and cavity
        print('x = ', x[-1], ' cost(x) = ', c[-1])
    else:
        c = [cost()]
        sign = np.sign(c[-1])
        

    eta = sign * step
    while True:
        if failure_threshold != None:
            if np.abs(c[-1]) > failure_threshold:
                return -999
        x_new = x[-1] - eta
        x.append(x_new)
        actuate(x_new)
        
        if test:
            c.append(cost(x[-1]))
            print('x = ', x[-1], ' cost(x) = ', c[-1])
#            time.sleep(.1)
        else:
            c.append(cost())
        if np.abs(c[-1]) < threshold:
            if full_output:
                return x, c
            else:
                return x[-1]
        
        if gradient:
            eta = (np.abs(c[-1]) - np.abs(c[-2]))/(x[-1]-x[-2]) * step
#            print('eta = ', eta)
        else:
            ''' Now correct the sign in case we're either moving in the wrong direction or overshot the minimum '''
            if (np.sign(c[-1]) != np.sign(c[-2])):          # this signals that we've crossed the minimum
                eta *= -0.5
#                print('Overshot minimum, decreasing step size')
#            elif np.abs(c[-1]) > np.abs(c[-2]):               # this signals that we're moving in the wrong direction
#                eta *= -.75
#                print('Correcting direction')
        if min_step != None and np.abs(eta) < min_step:
            eta = min_step * np.sign(eta)
            
        
        
    return
def gradient_descent(x0, cost, actuator, dither, gain, threshold, full_output = False, adaptive_gain = True, fixed_step = False, test = False):
    ''' A gradient descent algorithm returning the value x that minimizes cost_function(x)
        Args:
            x0 (float): initial guess
            cost_function: a function we are trying to minimize
            actuator_function: a method which takes a value x' and physically adjusts x -> x', returning the new value
            dither: the step size to use for gradient calculation
            gain: multiplicative factor for steps along the gradient
            threshold: absolute value of maximal accepted cost
            full_output: if True, return a list of all points sampled; otherwise, return only the last point
            adaptive_gain: if True, multiply the gain by x/threshold at all points; this tends to reduce oscillatory behavior, but can slow convergence
    '''
    x = [x0]
    if test:
        c = [cost(x[-1])]
    else:
        c = [cost()]
        
    while True:
        ''' Compute gradient '''
        if test:
            upper = cost(actuator(x[-1]+dither/2))
            lower = cost(actuator(x[-1]-dither/2))
        else:
            actuator(x[-1]+dither/2)
            upper = cost()
            actuator(x[-1]-dither/2)
            lower = cost()
        c.append((upper+lower)/2)
        gradient = (upper - lower) / dither
        
        ''' Move in direction of gradient ''' 
        
        if adaptive_gain: 
            x_new = x[-1] - c[-1]*gain*gradient
        else:
            x_new = x[-1]-gain*gradient
        if fixed_step:
            x_new = x[-1]-gain*np.sign(gradient)
        print('gradient: ', gradient, 'x: ', x[-1], ' x_new: ', x_new)
        x.append(x_new)
        actuator(x[-1])
        if np.abs(cost(x[-1])) < threshold:
            if full_output:
                return x, c
            else: 
                return x[-1]
#        print(x[-1])
            
   
def gaussian_cost(x):
    return 1-np.exp(-x**2)

def noisy_linear_cost(x):
    return x + np.random.uniform(0,.015)

def test_actuator(x):
    return x

if __name__ == '__main__':
#    x, c = gradient_descent(x0 = 1, cost = gaussian_cost, actuator = test_actuator, dither = .01, gain = .4, threshold = .00000001, full_output = True, adaptive_gain = False, test=True)
#    plt.plot(x)
#    plt.plot(c)
    x, c = line_search(x0 = 3, cost = noisy_linear_cost, actuate = test_actuator, step = .11, threshold = .001, full_output = True, test=True, gradient=True)
    plt.plot(x)
    plt.plot(c)

''' Dither-based gradient descent needs 3x as many measurements as line search. It may be more efficient to build in automatic gradient knowledge into the line search. '''

        
        