from emergent.utilities.containers import Parameter
import numpy as np
from emergent.utilities.plotting import plot_2D
from emergent.pipeline import Block

class GridSearch(Block):
    def __init__(self, params={}, state=None, bounds=None, cost=None, substate=None):
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
        super().__init__(state, bounds, cost, substate)

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
                c = self.pipeline.measure(point)
                points = np.append(points, np.atleast_2d(point), axis=0)
                costs = np.append(costs, c)

        best_point = points[np.argmin(costs)]
        _points = np.append(points, np.atleast_2d(best_point), axis=0)
        self.costs = np.append(costs, self.pipeline.measure(points[-1]))

        self.points = self.pipeline.unnormalize(points)
        return _points, self.costs      # return normalized points
