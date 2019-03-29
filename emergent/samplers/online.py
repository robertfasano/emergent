from emergent.utilities.containers import Parameter
import numpy as np
from emergent.utilities.plotting import plot_2D
from emergent.samplers.sampling import Sampling
import logging as log

class Online(Sampling):
    def __init__(self, sampler = None):
        ''' Define default parameters '''
        super().__init__(sampler)
        self.name = 'Online'
        self.params['Presampled points'] = Parameter(name= 'Presampled points',
                                            value = 15,
                                            min = 0,
                                            max = 100,
                                            description = 'Pre-sampled points before starting regression')
        self.params['Iterations'] = Parameter(name= 'Iterations',
                                            value = 10,
                                            min = 1,
                                            max = 10,
                                            description = 'Number of sample/fit cycles')
        self.params['Batch size'] = Parameter(name= 'Batch size',
                                            value = 10,
                                            min = 1,
                                            max = 100,
                                            description = 'Points sampled per iteration')
        self.params['Tolerance'] = Parameter(name= 'Tolerance',
                                            value = 0.01,
                                            min = 1e-4,
                                            max = 1e-1,
                                            description = 'Relative tolerance required for convergence')
        self.params['Mode'] = Parameter(name='Mode',
                                           value = ['Optimizer', 'Explorer', 'Hybrid'],
                                           description = 'Peak-seeking behavior.')

    def _run(self, state):
        ''' Perform initial random sampling '''
        if self.params['Mode'].value in ['Optimizer', 'Explorer']:
            log.warning('Overriding batch size to 1 for selected mode.')
            self.params['Batch size'].value = 1

        if self.sampler.model.imported:
            log.warning('Overriding presampling selection with loaded model.')
        else:
            log.info('Randomly sampling to pre-train model.')
            X, c = self.sampler.sample(state, 'random_sampling', self.params['Presampled points'].value)
            self.sampler.model.append(X, c)

            log.info('Training model.')
            self.sampler.model.fit()

        best_costs = []
        for i in range(int(self.params['Iterations'].value)):
            if not self.sampler.callback():
                self.points = self.sampler.model.points
                self.costs = self.sampler.model.costs
                return self.sampler.model.points[0:len(self.sampler.model.costs)], self.sampler.model.costs

            log.info('Sampling batch %i'%(i+1))
            a = i / (self.params['Iterations'].value-1)        # scale from explorer to optimizer through iterations
            for j in range(int(self.params['Batch size'].value)):
                if self.params['Batch size'].value > 1:
                    # b = a * j / (self.params['Batch size'].value-1)        # scale from explorer to optimizer throughout batch
                    b = j / (self.params['Batch size'].value-1)        # scale from explorer to optimizer throughout batch

                else:
                    b = 1
                if self.params['Mode'].value == 'Explorer':
                    b = 0
                elif self.params['Mode'].value == 'Optimizer':
                    b = 1
                new_point = self.sampler.model.next_sample(b=b)
                new_cost = self.sampler._cost(new_point)
                self.sampler.model.append(new_point, new_cost)

            log.info('Training model.')
            self.sampler.model.fit()

            ''' Evaluate best point for convergence check '''
            best_point = self.sampler.model.next_sample(b=1)
            best_cost = self.sampler._cost(best_point)
            self.sampler.model.append(best_point, best_cost)

            best_costs.append(best_cost)
            if len(best_costs) > 1:
                if np.abs((best_costs[-1] - best_costs[-2])/best_costs[-2])< self.params['Tolerance'].value:
                    break

        self.points = self.sampler.model.points
        self.costs = self.sampler.model.costs

        return self.points, self.costs

    def plot(self):
        return None
