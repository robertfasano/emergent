from emergent.utilities.containers import Parameter
import numpy as np
from emergent.utilities.plotting import plot_2D
from emergent.pipeline import Block
import logging as log

class GradientDescent(Block):
    def __init__(self, params={}):
        super().__init__()
        self.params = {}

        self.params['Iterations'] = Parameter(name = 'Iterations', type=int, value = 10)
        self.params['Learning rate'] = Parameter(name = 'Learning rate', value = 0.1)
        self.params['Dither size'] = Parameter(name = 'Dither size', value = 0.01)

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
        ''' Performs a uniformly-spaced sampling of the cost function in the
            space spanned by the passed-in state dict. '''
        if bounds is not None:
            log.warn('GradientDescent optimizer does not support bounds!')
        for i in range(self.params['Iterations'].value):
            x_i = points[-1]
            gradient, points, costs = self.gradient(points, costs)
            x_i -= self.params['Learning rate'].value * gradient
            points = np.append(points, np.atleast_2d(x_i), axis=0)
            costs = np.append(costs, self.pipeline.measure(x_i))
        self.points = self.pipeline.unnormalize(points)
        self.costs = costs
        return points, costs
