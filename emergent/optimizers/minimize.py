from utility import Parameter, algorithm
import numpy as np
from scipy.optimize import minimize

class Minimize():
    def __init__(self):
        ''' Define default parameters '''
        self.name = 'Minimize'
        self.params = {}
        self.params['Tolerance'] = Parameter(name= 'Tolerance',
                                            value = 0.01,
                                            min = 0.001,
                                            max = 0.1,
                                            description = 'Convergence criterion')

    @algorithm
    def run(self, state, cost, params={'Tolerance':1e-7}, cost_params = {}):
        ''' Runs a specified scipy minimization method on the target axes and cost. '''
        arr, bounds = self.sampler.initialize(state, cost, params, cost_params)
        keys = list(state.keys())
        res = minimize(fun=self.sampler._cost,
                   x0=arr,
                   bounds=bounds,
                   args = (state,),
                   method='L-BFGS-B',
                   tol = params['Tolerance'])
