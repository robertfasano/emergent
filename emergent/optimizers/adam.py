from utility import Parameter, algorithm
import numpy as np
import matplotlib.pyplot as plt

class Adam():
    def __init__(self):
        ''' Define default parameters '''
        self.name = 'Adam'
        self.params = {}
        self.params['Learning rate'] = Parameter(name= 'Learning rate',
                                            value = 0.1,
                                            min = 0.001,
                                            max = 0.1,
                                            description = 'Scaling factor for steps along the gradient')
        self.params['Tolerance'] = Parameter(name= 'Tolerance',
                                            value = 0.01,
                                            min = 0.001,
                                            max = 0.05,
                                            description = 'Convergence is detected when the gradient is this fraction of the max gradient')
        self.params['Dither'] = Parameter(name= 'Dither',
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
        self.params['noise'] = Parameter(name= 'noise',
                                            value = 0,
                                            min = 0,
                                            max = 0.1,
                                            description = 'Noise injection for stochastic optimization')
        self.params['restarts'] = Parameter(name= 'restarts',
                                            value = 3,
                                            min = 0,
                                            max = 10,
                                            description = 'Number of restarts allowed after divergence')
    @algorithm
    def run(self, state):
        arr, bounds = self.sampler.prepare(state)
        costs = [self.sampler._cost(arr)]
        points = [arr]
        m = np.zeros(len(arr))
        v = np.zeros(len(arr))
        epsilon = 1e-8
        gradients = []
        restarts = 0
        while True:
            ''' compute gradient '''
            g = self.sampler.estimate_gradient(arr, self.params['Dither'].value)
            gradients.append(g)

            gmag = np.dot(g,g)
            max_gmag = np.dot(np.max(gradients), np.max(gradients))
            if gmag/max_gmag < self.params['Tolerance'].value:
                if costs[-1] < costs[0]:
                    break
                else:
                    if restarts < self.params['restarts'].value:
                        points.append(points[np.argmin(costs)])
                        costs.append(self.sampler._cost(points[-1]))
                        restarts += 1
                        continue
                    else:
                        return
            m = self.params['beta_1'].value*m+(1-self.params['beta_1'].value)*g
            v = self.params['beta_2'].value*v + (1-self.params['beta_2'].value)*g**2

            mhat = m/(1-self.params['beta_1'].value)
            vhat = v/(1-self.params['beta_2'].value)

            ''' move along gradient '''
            arr = arr - self.params['Learning rate'].value*mhat/(np.sqrt(vhat)+epsilon)+np.random.normal(0, self.params['noise'].value, size=arr.shape)
            points.append(arr)
            costs.append(self.sampler._cost(arr))



        self.sampler._cost(arr)

    def set_params(self, params):
        for p in params:
            self.params[p].value = params[p]

    def plot(self):
        return plt.figure()
