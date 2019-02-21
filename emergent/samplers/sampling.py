from emergent.utilities.containers import Parameter
import numpy as np
from emergent.utilities.plotting import plot_2D

class Sampling():
    def __init__(self, sampler = None):
        ''' Define default parameters '''
        self.name = 'Sampling'
        self.sampler = sampler
        self.params = {}

    def _finish(self):
        ''' If a model has been attached to the sampler, fit it now '''
        if self.sampler.model is not None:
            self.sampler.model.append(self.points, self.costs)
            self.sampler.model.fit()

        if self.end_at == 'First point':
            last_point = self.points[0]
        elif self.end_at == 'Last point':
            last_point = self.points[-1]
        else:
            if self.sampler.model is not None:
                last_point = self.sampler.model.minimum()
            else:
                last_point = self.points[np.argmin(self.costs)]
        self.sampler._cost(last_point)

    def run(self, state):
        self._run(state)
        self._finish()
        return self.points, self.costs

    def _run(self, state):
        ''' Overload with specific sampling method. '''
        return self.points, self.costs

    def set_params(self, params):
        for p in params:
            self.params[p].value = params[p]

    def plot(self):
        return plot_2D(self.points, -self.costs, limits=self.sampler.get_limits())
