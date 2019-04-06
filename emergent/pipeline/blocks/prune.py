import numpy as np
from emergent.pipeline import Block
from emergent.utilities.containers import Parameter

class Prune(Block):
    def __init__(self, params={}):
        super().__init__()
        self.params = {'threshold': Parameter(name='Threshold', value=0.5)}
        for p in params:
            self.params[p] = params[p]

    def run(self, points, costs, bounds=None):
        valid_points = points[costs<np.min(costs)*self.params['threshold'].value]
        valid_costs = costs[costs<np.min(costs)*self.params['threshold'].value]

        return valid_points, valid_costs

    def _run(self, points, costs, bounds=None):
        return self.run(points, costs, bounds)
