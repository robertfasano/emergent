from emergent.utilities.containers import Parameter
from emergent.utilities.decorators import algorithm
import numpy as np
from emergent.utilities.plotting import plot_2D
from emergent.samplers.grid import GridSampling

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
        self.params['Sweeps'] = Parameter(name= 'Sweeps',
                                            value = 1,
                                            min = 1,
                                            max = 10,
                                            description = 'Number of sweeps to do')

    @algorithm
    def run(self, state):
        ''' An N-dimensional grid search (brute force) optimizer. '''
        # no longer uses params
        ''' Generate search grid '''
        self.points, self.costs = self.sampler.grid_sampling(state, self.params['Steps'].value, sweeps = self.params['Sweeps'].value)

        best_point = self.sampler.array2state(self.points[np.argmin(self.costs)])
        self.sampler._cost(best_point)

    # @algorithm
    # def run(self, state):
    #     sampler = GridSampling(self.sampler)
    #     sampler.set_params(self.params)
    #     self.points, self.costs = sampler.run(state)
    #     best_point = self.sampler.array2state(self.points[np.argmin(self.costs)])
    #     self.sampler._cost(best_point)

    def set_params(self, params):
        for p in params:
            self.params[p].value = params[p]

    def plot(self):
        return plot_2D(self.points, -self.costs, limits=self.sampler.get_limits())
