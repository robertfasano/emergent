from emergent.utilities.containers import Parameter
from emergent.utilities.decorators import algorithm
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, WhiteKernel
from scipy.optimize import minimize
from emergent.utilities.plotting import plot_2D
from emergent.models.model import Model
from scipy.optimize import curve_fit



class GaussianModel(Model):
    def __init__(self, optimizer, params = {}):
        self.optimizer = optimizer
        self.optimizer.source = self
        self.params = {}
        for p in params:
            self.params[p].value = params[p]

    def gaussian(self, X, *args):
        ''' Args:
                X: an N-element array representing a generally multidimensional point
                args:  first element: amplitude; next N: center; next N: width
        '''
        X = np.atleast_2d(X)
        N = X.shape[1]
        A = args[0]
        X0 = args[1:N+1]
        sigma = args[N+1:2*N+1]
        result = A
        for i in range(X.shape[1]):
            result *= np.exp(-(X[:,i]-X0[i])**2/sigma[i]**2)
        return result

    def fit(self, points, costs):
        N = points.shape[1]
        p0 = tuple([0.5]*(2*N+1))
        self.popt, self.pcov = curve_fit(self.gaussian, points, costs, p0)

    def predict(self, X):
        return self.gaussian(X, *tuple(self.popt)), 0

    def measure(self, X):
        return self.predict(X)[0][0]


    def run(self, points, costs, bounds=None):
        ''' Trains on the passed data, numerically optimizes the modeled response
            surface, then makes a physical measurement at the modeled minimum. '''
        self.fit(points, costs)
        x_pred, y_pred = self.optimizer.run(points, costs, bounds)
        point = points[np.argmin(costs)]
        best_point, best_cost = point, np.array([self.source.measure(point)])
        points = np.append(points, np.atleast_2d(best_point), axis=0)
        costs = np.append(costs, best_cost)

        return points, costs
