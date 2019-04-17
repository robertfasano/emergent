from emergent.utilities.containers import Parameter
from emergent.utilities.decorators import algorithm
import numpy as np
import matplotlib.pyplot as plt
from emergent.pipeline import Block
import logging as log

class Adam(Block):
    def __init__(self, params={}):
        super().__init__()
        ''' Define default parameters '''
        self.name = 'Adam'
        self.params = {}
        self.params['Learning rate'] = Parameter(name= 'Learning rate',
                                            value = 0.1,
                                            description = 'Scaling factor for steps along the gradient')
        self.params['Tolerance'] = Parameter(name= 'Tolerance',
                                            value = 0.01,
                                            description = 'Convergence is detected when the gradient is this fraction of the max gradient')
        self.params['Dither size'] = Parameter(name = 'Dither size',
                                            value = 0.01,
                                            description = 'Step size for gradient estimation')
        self.params['Beta_1'] = Parameter(name= 'Beta_1',
                                            value = 0.9,
                                            min = 0.8,
                                            max = 0.99,
                                            description = 'Exponential decay rate for first-moment estimates')
        self.params['Beta_2'] = Parameter(name= 'Beta_2',
                                            value = 0.999,
                                            min = 0.9,
                                            max = 0.999,
                                            description = 'Exponential decay rate for second-moment estimates')
        self.params['Noise'] = Parameter(name= 'Noise',
                                            value = 0,
                                            description = 'Noise injection for stochastic optimization')
        for p in params:
            self.params[p].value = params[p]

    def gradient(self, points, costs):
        point = points[-1]
        dim = points.shape[1]
        g = np.zeros(dim)
        for d in range(dim):
            step = np.zeros(dim)
            step[d] = self.params['Dither size'].value

            p1 = point + step
            p2 = point - step
            c1 = self.pipeline.measure(p1)
            c2 = self.pipeline.measure(p2)
            g[d] = (c1-c2)/(2*step[d])

            for p in [p1, p2]:
                points = np.append(points, np.atleast_2d(p), axis=0)
            for c in [c1, c2]:
                costs = np.append(costs, c)
        return g, points, costs

    def run(self, points, costs, bounds=None):
        if bounds is not None:
            log.warn('Adam optimizer does not support bounds!')
        dim = points.shape[1]
        m = np.zeros(dim)
        v = np.zeros(dim)
        epsilon = 1e-8
        gradients = []
        while True:
            ''' compute gradient '''
            x_i = points[-1]
            g, points, costs = self.gradient(points, costs)
            gradients.append(g)
            gmag = np.dot(g,g)
            max_gmag = np.dot(np.max(gradients), np.max(gradients))
            if gmag/max_gmag < self.params['Tolerance'].value:
                break

            m = self.params['Beta_1'].value*m+(1-self.params['Beta_1'].value)*g
            v = self.params['Beta_2'].value*v + (1-self.params['Beta_2'].value)*g**2

            mhat = m/(1-self.params['Beta_1'].value)
            vhat = v/(1-self.params['Beta_2'].value)

            ''' move along gradient '''
            x_i -= self.params['Learning rate'].value*mhat/(np.sqrt(vhat)+epsilon)+np.random.normal(0, self.params['Noise'].value, size=dim)
            points = np.append(points, np.atleast_2d(x_i), axis=0)
            costs = np.append(costs, self.pipeline.measure(x_i))

        return points, costs
