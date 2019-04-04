from emergent.utilities.containers import Parameter
import numpy as np
from emergent.utilities.plotting import plot_2D
from emergent.pipeline import Block

class GridSearch(Block):
    def __init__(self, params={}):
        super().__init__()
        self.params = {}

        self.params['Steps'] = Parameter(name= 'Steps',
                                            type = int,
                                            value = 20,
                                            description = 'Grid points per dimension')
        self.params['Sweeps'] = Parameter(name= 'Sweeps',
                                            value = 1,
                                            type = int,
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
                space = np.linspace(0, 1, self.params['Steps'].value)
            else:
                space = np.linspace(bounds[n][0], bounds[n][1], self.params['Steps'].value)
            grid.append(space)
        grid = np.array(grid)
        grid_points = np.transpose(np.meshgrid(*[grid[n] for n in range(dim)])).reshape(-1, dim)

        ''' Actuate search '''
        grid_costs = np.array([])
        for i in range(self.params['Sweeps'].value):
            for point in grid_points:
                # if not self.sampler.callback():
                #     return self.points[0:len(self.costs)], self.costs
                c = self.measure(point)

                grid_costs = np.append(grid_costs, c)

        points = np.append(points, grid_points, axis=0)
        costs = np.append(costs, grid_costs)

        best_point = points[np.argmin(costs)]
        points = np.append(points, np.atleast_2d(best_point), axis=0)
        costs = np.append(costs, self.measure(points[-1]))
        return points, costs
