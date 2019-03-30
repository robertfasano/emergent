import numpy as np
from emergent.pipeline import Block

class Prune(Block):
    def __init__(self, threshold=0.5):
        super().__init__()
        self.threshold = threshold

    def run(self, points, costs, bounds=None):
        valid_points = points[costs<np.min(costs)*self.threshold]
        valid_costs = costs[costs<np.min(costs)*self.threshold]

        return valid_points, valid_costs

    def _run(self, points, costs, bounds=None):
        return self.run(points, costs, bounds)
