import numpy as np
from emergent.pipeline import Block
from emergent.utilities.containers import Parameter

class Rescale(Block):
    def __init__(self, params={}):
        super().__init__()
        self.params = {'Threshold': Parameter(name='Threshold', value=0.5)}
        for p in params:
            self.params[p].value = params[p]

    def run(self, points, costs, bounds=None):
        valid_points = points[costs<np.min(costs)*self.params['Threshold'].value]
        new_bounds = []
        for i in range(points.shape[1]):
            new_bounds.append((valid_points[:,i].min(), valid_points[:,i].max()))
        self.pipeline.bounds = new_bounds
        return points, costs
