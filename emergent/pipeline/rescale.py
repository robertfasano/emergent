import numpy as np
from emergent.pipeline import Block

class Rescale(Block):
    def __init__(self, threshold=0.5):
        super().__init__()
        self.threshold = threshold

    def run(self, points, costs, bounds=None):
        valid_points = points[costs<np.min(costs)*self.threshold]
        new_bounds = []
        for i in range(points.shape[1]):
            new_bounds.append((valid_points[:,i].min(), valid_points[:,i].max()))
        self.pipeline.bounds = new_bounds
        return points, costs
