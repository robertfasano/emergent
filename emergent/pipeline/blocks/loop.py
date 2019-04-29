from emergent.pipeline import BasePipeline
from emergent.utilities.containers import Parameter

class Loop(BasePipeline):
    def __init__(self, params = {'Loops': 1}):
        super().__init__()
        self.params = {}
        self.params['Loops'] = Parameter(name='Loops',
                                         value=1,
                                         type=int)
        for p in params:
            self.params[p].value = params[p]

    def measure(self, point):
        return self.pipeline.measure(point)

    def run(self, points, costs, bounds=None):
        self.bounds = self.pipeline.bounds
        self.points = points.copy()
        self.costs = costs.copy()
        for i in range(self.params['Loops'].value):
            for block in self.blocks:
                self.points, self.costs = block.run(self.points, self.costs, self.bounds)
                self.pipeline.bounds = self.bounds # update parent bounds in case they changed
        return self.points, self.costs

    def unnormalize(self, points):
        return self.pipeline.unnormalize(points)
