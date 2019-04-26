from emergent.utilities.containers import Parameter
import numpy as np
from scipy.optimize import differential_evolution
import itertools
from emergent.pipeline import Block

class DifferentialEvolution(Block):
    def __init__(self, params={}, state=None, bounds=None, cost=None, substate=None):
        super().__init__()
        self.params = {}
        self.params['Population'] = Parameter(name= 'Population',
                                            value = 20,
                                            type = int,
                                            description = 'Initial population size')
        self.params['Tolerance'] = Parameter(name= 'Tolerance',
                                            value = 0.01,
                                            description = 'Convergence criterion')
        self.params['Mutation'] = Parameter(name= 'Population size',
                                            value = 1,
                                            min = 0,
                                            max = 2,
                                            description = 'Mutation constant in [0,2]. Larger values increase search radius but slow down convergence.')
        self.params['Recombination'] = Parameter(name= 'Recombination',
                                            value = 0.7,
                                            min = 0,
                                            max = 1,
                                            description = 'Crossover probability. Increasing this value allows a larger number of mutants to progress into the next generation, but at the risk of population stability.')
        for p in params:
            self.params[p].value = params[p]
        super().__init__(state, bounds, cost, substate)
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
        ''' Differential evolution algorithm from scipy.optimize. '''
        if bounds is None:
            bounds = np.array(list(itertools.repeat([0, 1], points.shape[1])))

        self.measured_points = None
        self.measured_costs = np.array([])
        res = differential_evolution(func=self._measure,
                   bounds=bounds,
                   strategy='best1bin',
                   tol = self.params['Tolerance'].value,
                   mutation = self.params['Mutation'].value,
                   recombination = self.params['Recombination'].value,
                   popsize = self.params['Population'].value)

        points = np.append(points, self.measured_points, axis=0)
        self.costs = np.append(costs, self.measured_costs, axis=0)
        self.points = self.pipeline.unnormalize(points)
        return points, self.costs
