from emergent.utilities.containers import Parameter
from emergent.utilities.decorators import algorithm
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, WhiteKernel
import pickle
from emergent.pipeline import Block

class GaussianProcess(Block):
    def __init__(self, optimizer, params={}):
        super().__init__()
        self.optimizer = optimizer
        self.optimizer.source = self
        self.params = {}
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
        for p in params:
            self.params[p].value = params[p]
        kernel = C(self.params['Amplitude'].value, (1e-3, 1e3)) * RBF(self.params['Length scale'].value, (1e-2, 1e2)) + WhiteKernel(self.params['Noise'].value)
        self.model = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10)

    def fit(self, points, costs):
        self.model.fit(points, costs)

    def predict(self, X):
        return self.model.predict(np.atleast_2d(X), return_std = True)

    def measure(self, X):
        return self.predict(X)[0][0]

    def run(self, points, costs, bounds=None):
        ''' Trains on the passed data, numerically optimizes the modeled response
            surface, then makes a physical measurement at the modeled minimum. '''
        self.fit(points, costs)
        x_pred, y_pred = self.optimizer.run(points, costs, bounds)
        x_pred = x_pred[len(points)::]
        y_pred = y_pred[len(costs)::]
        point = x_pred[np.argmin(y_pred)]
        best_point, best_cost = point, np.array([self.source.measure(point)])
        points = np.append(points, np.atleast_2d(best_point), axis=0)
        costs = np.append(costs, best_cost)

        return points, costs