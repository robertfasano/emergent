from emergent.utilities.containers import Parameter
from emergent.utilities.decorators import algorithm
import numpy as np
from emergent.models.GPR import GaussianProcess

class NewGaussianProcessRegression():
    def __init__(self):
        ''' Define default parameters '''
        self.name = 'NewGaussianProcessRegression'
        self.params = {}
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
        self.params['Amplitude'] = Parameter(name= 'Kernel amplitude',
                                            value = 1,
                                            min = 0,
                                            max = 10,
                                            description = 'Amplitude of modeled cost landscape')
        self.params['Length scale'] = Parameter(name= 'Kernel length scale',
                                            value = 1,
                                            min = 0,
                                            max = 10,
                                            description = 'Characteristic size of cost landscape')
        self.params['Noise'] = Parameter(name= 'Kernel noise',
                                            value = 0.1,
                                            min = 0,
                                            max = 10,
                                            description = 'Amplitude of modeled white noise process')
        self.params['Tolerance'] = Parameter(name= 'Tolerance',
                                            value = 0.01,
                                            min = 1e-4,
                                            max = 1e-1,
                                            description = 'Relative tolerance required for convergence')
        self.params['Leash'] = Parameter(name= 'Leash',
                                            value = 0.25,
                                            min = 0.01,
                                            max = 0.25,
                                            description = 'Allowed search range relative to last best point')

    @algorithm
    def run(self, state):
        ''' Online Gaussian process regression. Batch sampling is done with
            points with varying trade-off of optimization vs. exploration. '''
        self.model = GPR(self.sampler, self.params)
        self.callback = self.sampler.callback
        X, c = self.sampler.sample(state, 'random_sampling', self.params['Presampled points'].value)
        self.model.append(X, c)
        best_costs = []
        for i in range(int(self.params['Iterations'].value)):
            if not self.callback():
                return self.model.points[0:len(self.model.costs)], self.model.costs
            self.model.fit()
            a = i / (self.params['Iterations'].value-1)        # scale from explorer to optimizer through iterations
            for j in range(int(self.params['Batch size'].value)):
                b = a * j / (self.params['Batch size'].value-1)        # scale from explorer to optimizer throughout batch
                new_point = self.model.next_sample(b=b)
                new_cost = self.sampler._cost(new_point)
                self.model.append(new_point, new_cost)

            ''' Evaluate best point for convergence check '''
            best_point = self.model.next_sample(b=1)
            best_cost = self.sampler._cost(best_point)
            self.model.append(best_point, best_cost)

            best_costs.append(best_cost)
            if len(best_costs) > 1:
                if np.abs((best_costs[-1] - best_costs[-2])/best_costs[-2])< self.params['Tolerance'].value:
                    break

        self.model.fit()
        best_point = self.sampler.array2state(self.model.points[np.argmin(self.model.costs)])
        self.sampler.actuate(self.sampler.unnormalize(best_point))

        return self.params

    def set_params(self, params):
        for p in params:
            self.params[p].value = params[p]

    def plot(self):
        ''' Predict and plot cost landscape '''
        return self.model.plot()
