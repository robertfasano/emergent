from utility import Parameter, algorithm
import numpy as np

class GridSearch():
    def __init__(self):
        ''' Define default parameters '''
        self.name = 'GridSearch'
        self.params = {}
        self.params['Steps'] = Parameter(name= 'Steps',
                                            value = 20,
                                            min = 5,
                                            max = 100,
                                            description = 'Grid points per dimension')

    @algorithm
    def run(self, state, cost, params={'Steps':10}, cost_params = {}):
        ''' An N-dimensional grid search (brute force) optimizer. '''
        arr, bounds = self.sampler.initialize(state, cost, params, cost_params)
        ''' Generate search grid '''
        points, costs = self.sampler.grid_sampling(state, cost, params, cost_params, params['Steps'])

        best_point = self.sampler.array2state(points[np.argmin(costs)])
        self.sampler.actuate(self.sampler.unnormalize(best_point))
        return points, costs
