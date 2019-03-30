from emergent.utilities.containers import Parameter
import numpy as np
from emergent.utilities.plotting import plot_2D

class GridSearch():
    def __init__(self, params={}):
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
        for p in params:
            self.params[p].value = params[p]

    def run(self, points, costs, bounds=None):
        ''' Performs a uniformly-spaced sampling of the cost function in the
            space spanned by the passed-in state dict. '''
        dim = points.shape[1]
        grid = []
        for n in range(dim):
            if bounds is None:
                space = np.linspace(0, 1, int(self.params['Steps'].value))
            else:
                space = np.linspace(bounds[n][0], bounds[n][1], int(self.params['Steps'].value))
            grid.append(space)
        grid = np.array(grid)
        grid_points = np.transpose(np.meshgrid(*[grid[n] for n in range(dim)])).reshape(-1, dim)

        ''' Actuate search '''
        grid_costs = np.array([])
        for i in range(int(self.params['Sweeps'].value)):
            for point in grid_points:
                # if not self.sampler.callback():
                #     return self.points[0:len(self.costs)], self.costs
                c = self.source.measure(point)

                grid_costs = np.append(grid_costs, c)

        points = np.append(points, grid_points, axis=0)
        costs = np.append(costs, grid_costs)
        return points, costs
