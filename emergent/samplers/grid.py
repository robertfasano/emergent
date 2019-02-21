from emergent.utilities.containers import Parameter
import numpy as np
from emergent.utilities.plotting import plot_2D

class GridSampling():
    def __init__(self, sampler = None):
        ''' Define default parameters '''
        self.name = 'GridSampling'
        self.sampler = sampler
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


    def run(self, state, go_to_best = False):
        ''' Performs a uniformly-spaced sampling of the cost function in the
            space spanned by the passed-in state dict. '''
        arr, bounds = self.sampler.prepare(state)
        dim = len(arr)
        grid = []
        for n in range(dim):
            space = np.linspace(bounds[n][0], bounds[n][1], int(self.params['Steps'].value))
            grid.append(space)
        grid = np.array(grid)
        self.points = np.transpose(np.meshgrid(*[grid[n] for n in range(dim)])).reshape(-1, dim)

        ''' Actuate search '''
        self.costs = np.array([])
        for i in range(int(self.params['Sweeps'].value)):
            for point in self.points:
                if not self.sampler.callback():
                    return self.points[0:len(self.costs)], self.costs
                c = self.sampler._cost(point)

                self.costs = np.append(self.costs, c)

        if go_to_best:
            best_point = self.sampler.array2state(self.points[np.argmin(self.costs)])
            self.sampler._cost(best_point)

        ''' If a model has been attached to the sampler, fit it now '''
        if self.sampler.model is not None:
            self.sampler.model.append(self.points, self.costs)
            self.sampler.model.fit()
        return self.points, self.costs

    def set_params(self, params):
        for p in params:
            self.params[p].value = params[p]

    def plot(self):
        return plot_2D(self.points, -self.costs, limits=self.sampler.get_limits())
