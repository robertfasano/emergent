import numpy as np
import matplotlib.pyplot as plt
import time


def line_search(x0, cost, actuate, step, threshold, full_output = False, test = False, gradient = False, min_step = None, failure_threshold = None, quit_function = None, x_max = None, x_min = None):
    ''' Requires an odd cost function '''
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
        if x_max != None and x_min != None:
            if x_new > x_max or x_new < x_min:
                print('Target actuation out of range!')
        if quit_function != None:
            if quit_function():
                print('Line search terminated!')
                return x[-1]
        if test:
            c.append(cost(x[-1]))
            print('x = ', x[-1], ' cost(x) = ', c[-1])
            time.sleep(.1)
        else:
#            print('x = ', x[-1], ' cost(x) = ', c[-1])
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

def oscillator(center, span, steps):
    step_size = span/steps
    array = [center]
    j = 1
    for i in range(steps-1):
        if i % 2:
            array.append(center + step_size * j)
        else:
            array.append(center - step_size * j)
            j += 1
    return array
    
def z_search(y):
    # Let y be a vector of timeseries data of at least length lag+2
    # Let mean() be a function that calculates the mean
    # Let std() be a function that calculates the standard deviaton
    # Let absolute() be the absolute value function
    
    # Settings (the ones below are examples: choose what is best for your data)
    lag = 10         # lag 5 for the smoothing functions
    threshold = 5 # 3.5 standard deviations for signal
    influence = .5  # between 0 and 1, where 1 is normal influence, 0.5 is half

    # Initialise variables
    signals = np.zeros(len(y))   # Initialise signal results
    filteredY = y[0:lag-1]                            # Initialise filtered series
    avgFilter = np.zeros(len(y))                         # Initialise average filter
    stdFilter = np.zeros(len(y))                    # Initialise std. filter
    avgFilter[lag-1] = np.mean(filteredY);    # Initialise first value
    stdFilter[lag-1] = np.std(filteredY);     # Initialise first value
    
    for i in range(lag-1, len(y)-1):
        if np.abs(y[i-1] - avgFilter[i-2]) > threshold*stdFilter[i-2]:
            if y[i-1] > avgFilter[i-2]:
                signals[i-1] = 1                     # Positive signal
            else:
                signals[i-1] = -1                     # Negative signal
            # Make influence lower
            filteredY = np.append(filteredY, influence*y[i] + (1-influence)*filteredY[i-1])
        else:
            signals[i-1] = 0                        # No signal
            filteredY = np.append(filteredY, y[i])
    
          # Adjust the filters
        avgFilter[i-1] = np.mean(filteredY[i-lag-1:i-1])
        stdFilter[i-1] = np.std(filteredY[i-lag-1:i-1])
      
    return signals, avgFilter, stdFilter
  
  
  
            
def peak_search(x0, signal, actuate, step, threshold, full_output = False, test = False, failure_threshold = None):
    ''' Seeks the maximum of an even function '''
    x = [x0]
    
    ''' Measure initial signal '''
    if test:
        s = [signal(x[-1])]
        print('x = ', x[-1], ' signal(x) = ', s[-1])
    else:
        s = [signal()]

    gradient = 1
    while True:
        eta = gradient * step / s[-1]

        if failure_threshold != None:
            if np.abs(s[-1]) > failure_threshold:
                return -999
        x_new = x[-1] - eta
        x.append(x_new)
        actuate(x_new)
        if test:
            s.append(signal(x[-1]))
#            print('x = ', x[-1], ' signal(x) = ', s[-1])
#            time.sleep(.1)
        else:
#            print('x = ', x[-1], ' cost(x) = ', c[-1])
            s.append(signal())
        gradient = (s[-1] - s[-2])/eta

        if np.abs(eta) < threshold:
            if full_output:
                return x, s
            else:
                return x[-1]
        

            
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

def lorentzian(x, gamma = 1, noise = .02):
    if type(x) in [int,float]:
        size = 1
    else:
        size = len(x)
    return 1/np.pi * gamma/2 / (x**2+gamma**2/4) +np.random.normal(0, noise, size = size)

def test_actuator(x):
    return x

if __name__ == '__main__':
#    x, c = gradient_descent(x0 = 1, cost = gaussian_cost, actuator = test_actuator, dither = .01, gain = .4, threshold = .00000001, full_output = True, adaptive_gain = False, test=True)
#    plt.plot(x)
#    plt.plot(c)
    line = np.arange(-10,10,.001)
#    plt.plot(line, lorentzian(line))
#    x, c = line_search(x0 = 3, cost = lorentzian, actuate = test_actuator, step = .3, threshold = .001, full_output = True, test=True, gradient=True)
#    x, c = oscillator_search(x0 = 3, signal = lorentzian, actuate = test_actuator, step = .01, threshold = .0001, full_output = True, test = True)
    s, mu, sigma = z_search(lorentzian(line))
    plt.plot(lorentzian(line))
#    x, c = gradient_descent(x0 = 3, cost = -lorentzian, actuate = test_actuator, step = .3, threshold = .001, full_output = True, test=True, gradient=False)

#    line1, = plt.plot(x, label='x')
#    line2, = plt.plot(c, label='Signal')
#    plt.legend()
#    
#    plt.figure()
#    line = np.arange(-3,3,.001)
#    x = np.array(x)
#    plt.plot(line, lorentzian(line))

''' Dither-based gradient descent needs 3x as many measurements as line search. It may be more efficient to build in automatic gradient knowledge into the line search. '''

        
        