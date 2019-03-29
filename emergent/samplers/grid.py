from emergent.utilities.containers import Parameter
import numpy as np
from emergent.utilities.plotting import plot_2D
from emergent.samplers.sampling import Sampling

class Grid(Sampling):
    def __init__(self, sampler=None, params={}):
        ''' Define default parameters '''
        super().__init__(sampler)
        self.name = 'Grid'
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
        for p in params:
            self.params[p].value = params[p]

    def _run(self, state):
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

        return self.points, self.costs
