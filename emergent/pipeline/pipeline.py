import numpy as np

class Pipeline:
    def __init__(self, state, source):
        self.source = source
        self.points = np.atleast_2d(source.scaler.state2array(source.scaler.normalize(state)))
        self.costs = np.array([source.measure(state)])

        self.bounds = []
        for d in range(self.points.shape[1]):
            self.bounds.append((0,1))

        self.blocks = []

    def add(self, block):
        self.blocks.append(block)
        block.source = self.source
        block.pipeline = self

    def run(self):
        for block in self.blocks:
            self.points, self.costs = block.run(self.points, self.costs, self.bounds)
        return self.points, self.costs
