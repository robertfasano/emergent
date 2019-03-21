from emergent.utilities.containers import Parameter
from emergent.utilities.decorators import algorithm
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, WhiteKernel
from emergent.models.model import Model
import pickle

class GaussianProcess(Model):
    def __init__(self):
        super().__init__('GaussianProcess')
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
        kernel = C(self.params['Amplitude'].value, (1e-3, 1e3)) * RBF(self.params['Length scale'].value, (1e-2, 1e2)) + WhiteKernel(self.params['Noise'].value)
        self.model = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10)
        self.extension = '.gp'

    def fit(self):
        self.model.fit(self.points, self.costs)

    def predict(self, X):
        return self.model.predict(np.atleast_2d(X), return_std = True)

    def _export(self):
        filename = self.sampler.hub.network.path['data'] + 'weights' + self.extension
        with open(filename, 'wb') as file:
            pickle.dump(self.model, file)

    def _import(self):
        filename = self.sampler.hub.network.path['data'] + 'weights' + self.extension
        with open(filename, 'rb') as file:
            self.model = pickle.load(file)
