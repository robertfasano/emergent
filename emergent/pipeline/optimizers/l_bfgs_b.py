from emergent.utilities.containers import Parameter
import numpy as np
from scipy.optimize import minimize
import itertools
from emergent.pipeline import Block

class LBFGSB(Block):
    def __init__(self, params={}):
        super().__init__()
        self.params = {}

        self.params['Tolerance'] = Parameter(name= 'Tolerance',
                                            value = 0.01,
                                            description = 'Convergence criterion')
        for p in params:
            self.params[p].value = params[p]

    def _measure(self, point):
        ''' Intermediate cost function only used to store the points and costs
            obtained by the differential evolution routine. '''
        if self.measured_points is None:
            self.measured_points = np.atleast_2d(point)
        else:
            self.measured_points = np.append(self.measured_points, np.atleast_2d(point), axis=0)
        c = self.pipeline.measure(point)
        self.measured_costs = np.append(self.measured_costs, c)

        return c

    def run(self, points, costs, bounds=None):
        ''' L-BFGS-B algorithm from scipy.optimize. '''
        if bounds is None:
            bounds = np.array(list(itertools.repeat([0, 1], points.shape[1])))

        self.measured_points = None
        self.measured_costs = np.array([])
        res = minimize(fun=self._measure,
                   x0=points[-1],
                   bounds=bounds,
                   method='L-BFGS-B',
                   tol = self.params['Tolerance'].value)

        points = np.append(points, self.measured_points, axis=0)
        self.costs = np.append(costs, self.measured_costs, axis=0)
        self.points = self.pipeline.unnormalize(points)
        return points, self.costs
