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
    def run(self, state):
        ''' An N-dimensional grid search (brute force) optimizer. '''
        # no longer uses params
        # arr, bounds = self.sampler.initialize(state, cost, params, cost_params)
        ''' Generate search grid '''
        points, costs = self.sampler.grid_sampling(state, self.params['Steps'].value)

        best_point = self.sampler.array2state(points[np.argmin(costs)])
        # self.sampler.actuate(self.sampler.unnormalize(best_point))
        self.sampler._cost(best_point)
        return points, costs

    def set_params(self, params):
        for p in params:
            self.params[p].value = params[p]
