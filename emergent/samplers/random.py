from emergent.utilities.containers import Parameter
import numpy as np
from emergent.utilities.plotting import plot_2D
from emergent.samplers.sampling import Sampling

class Random(Sampling):
    def __init__(self, sampler = None):
        ''' Define default parameters '''
        super().__init__(sampler)
        self.name = 'Random'
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

    def _run(self, state):
        ''' Performs a uniformly-spaced sampling of the cost function in the
            space spanned by the passed-in state dict. '''
        dof = sum(len(state[x]) for x in state)
        self.points = np.random.uniform(size=(int(self.params['Steps'].value),dof))
        self.costs = np.array([])
        for point in self.points:
            if not self.sampler.callback():
                return self.points[0:len(self.costs)], self.costs
            c = self.sampler._cost(point)
            self.costs = np.append(self.costs, c)

    def plot(self):
        return None
