import numpy as np


def holder_table(state, params):
    x = state['X']
    y = state['Y']
    return -np.abs(np.sin(x)*np.cos(y)*np.exp(np.abs(1-np.sqrt(x**2+y**2)/np.pi)))

def himmelblau(state, params):
    x = state['X']
    y = state['Y']

    return (x**2+y-11)**2+(x+y**2-7)**2


def ackley(state, params):
    x = state['X']
    y = state['Y']
    result = -20*np.exp(-0.2*np.sqrt(0.5*(x**2+y**2)))
    result -= np.exp(0.5*(np.cos(2*np.pi*x)+np.cos(2*np.pi*y)))
    result += e + 20
    return result

def rosenbrock(state, params):
    x = state['X']
    y = state['Y']
    a = 1
    b = 100
    return (a-x)**2+b*(y-x**2)**2
