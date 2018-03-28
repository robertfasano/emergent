import numpy as np
import matplotlib.pyplot as plt
import time

def gradient_descent(x0, cost, actuator, dither, gain, threshold, full_output = False, adaptive_gain = True, fixed_step = False):
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

    while True:
        ''' Compute gradient '''
        upper = cost(actuator(x[-1]+dither/2))
        lower = cost(actuator(x[-1]-dither/2))
        gradient = (upper - lower) / dither
        
        ''' Move in direction of gradient ''' 
        if adaptive_gain: 
            x_new = x[-1] - cost(actuator(x[-1]))*gain*gradient
#            print('gradient: ', gradient, 'x: ', x[-1], ' x_new: ', x_new)
        else:
            x_new = x[-1]-gain*gradient
        if fixed_step:
            x_new = x[-1]-gain*np.sign(gradient)
        x.append(actuator(x_new))
        if np.abs(cost(x[-1])) < threshold:
            if full_output:
                return x
            else: 
                return x[-1]
#        print(x[-1])
            
   
def gaussian_cost(x):
    return 1-np.exp(-x**2)

def test_actuator(x):
    return x

if __name__ == '__main__':
    plt.plot(gradient_descent(x0 = 1, cost = gaussian_cost, actuator = test_actuator, dither = .01, gain = 5, threshold = .001, full_output = True, adaptive_gain = True))
        
        