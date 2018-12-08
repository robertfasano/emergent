from utility import Parameter, algorithm
import numpy as np

class DifferentialEvolution():
    def __init__(self):
        ''' Define default parameters '''
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

    @algorithm
    def run(self, state, cost, params={'Population':15, 'Tolerance':0.01, 'Mutation': 1,'Recombination':0.7}, cost_params = {}):
        ''' Differential evolution algorithm from scipy.optimize. '''
        X, bounds = self.sampler.initialize(state, cost, params, cost_params)
        keys = list(state.keys())
        res = differential_evolution(func=self.sampler._cost,
                   bounds=bounds,
                   args = (state,),
                   strategy='best1bin',
                   tol = params['Tolerance'],
                   mutation = params['Mutation'],
                   recombination = params['Recombination'],
                   popsize = params['Population'])
