from emergent.utilities.containers import Parameter
import numpy as np
from scipy.optimize import differential_evolution
import itertools

class DifferentialEvolution():
    def __init__(self, params={}):
        self.name = 'DifferentialEvolution'
        self.params = {}
        self.params['Population'] = Parameter(name= 'Population',
                                            value = 20,
                                            min = 5,
                                            max = 100,
                                            description = 'Initial population size')
        self.params['Tolerance'] = Parameter(name= 'Tolerance',
                                            value = 0.01,
                                            min = 0.001,
                                            max = 0.1,
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

    def run(self, points, costs, bounds=None):
        ''' Differential evolution algorithm from scipy.optimize. '''
        if bounds is None:
            bounds = np.array(list(itertools.repeat([0, 1], points.shape[1])))

        res = differential_evolution(func=self.source.measure,
                   bounds=bounds,
                   strategy='best1bin',
                   tol = self.params['Tolerance'].value,
                   mutation = self.params['Mutation'].value,
                   recombination = self.params['Recombination'].value,
                   popsize = int(self.params['Population'].value))

        points = np.append(points, np.atleast_2d(res.x), axis=0)
        costs = np.append(costs, np.array([res.fun]))
        return points, costs
