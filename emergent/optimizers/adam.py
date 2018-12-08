from utility import Parameter, algorithm
import numpy as np

class Adam():
    def __init__(self):
        ''' Define default parameters '''
        self.name = 'Adam'
        self.params = {}
        self.params['learning rate'] = Parameter(name= 'Learning rate',
                                            value = 0.1,
                                            min = 0.001,
                                            max = 0.1,
                                            description = 'Scaling factor for steps along the gradient')
        self.params['iterations'] = Parameter(name= 'Iterations',
                                            value = 100,
                                            min = 10,
                                            max = 1000,
                                            description = 'Number of iterations')
        self.params['dither'] = Parameter(name= 'Dither',
                                            value = 0.01,
                                            min = 0.0001,
                                            max = 0.1,
                                            description = 'Step size for gradient estimation')
        self.params['beta_1'] = Parameter(name= 'beta_1',
                                            value = 0.9,
                                            min = 0.8,
                                            max = 0.99,
                                            description = 'Exponential decay rate for first-moment estimates')
        self.params['beta_2'] = Parameter(name= 'beta_2',
                                            value = 0.999,
                                            min = 0.9,
                                            max = 0.999,
                                            description = 'Exponential decay rate for second-moment estimates')

    @algorithm
    def run(self, state, cost, params={'Learning rate':1, 'Iterations': 100, 'Dither': 0.01, 'beta_1': 0.9, 'beta_2': 0.999}, cost_params = {}):
        arr, bounds = self.sampler.initialize(state, cost, params, cost_params)
        m = np.zeros(len(arr))
        v = np.zeros(len(arr))
        epsilon = 1e-8
        for s in range(int(params['Iterations'])):
            ''' compute gradient '''
            g = self.sampler.estimate_gradient(arr, params['Dither'])
            m = params['beta_1']*m+(1-params['beta_1'])*g
            v = params['beta_2']*v + (1-params['beta_2'])*g**2

            mhat = m/(1-params['beta_1'])
            vhat = v/(1-params['beta_2'])

            ''' move along gradient '''
            arr = arr - params['Learning rate']*mhat/(np.sqrt(vhat)+epsilon)

        self.sampler._cost(arr)
