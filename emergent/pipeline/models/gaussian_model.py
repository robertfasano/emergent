from emergent.utilities.containers import Parameter
from emergent.utilities.decorators import algorithm
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, WhiteKernel
from scipy.optimize import minimize
from emergent.utilities.plotting import plot_1D, plot_2D
from scipy.optimize import curve_fit
from emergent.pipeline import Block
import matplotlib.pyplot as plt

class GaussianModel(Block):
    def __init__(self, optimizer, params = {}):
        super().__init__()
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
        x_pred = x_pred[len(points)::]
        y_pred = y_pred[len(costs)::]
        point = x_pred[np.argmin(y_pred)]
        self.best_point, best_cost = point, np.array([self.source.measure(point)])
        points = np.append(points, np.atleast_2d(self.best_point), axis=0)
        costs = np.append(costs, best_cost)

        return points, costs

    def plot(self, axis1, axis2=None, n_points = 30):
        dim = len(self.best_point)
        x = np.linspace(self.pipeline.bounds[axis1][0],
                        self.pipeline.bounds[axis1][1],
                        n_points)
        if axis2 is not None:
            y = np.linspace(self.pipeline.bounds[axis2][0],
                            self.pipeline.bounds[axis2][1],
                            n_points)
            points = np.transpose(np.meshgrid(x,y)).reshape(-1, dim)
            data = np.ones((n_points**2, dim))
            for d in range(dim):
                data[:, d] = self.best_point[d]
            data[:, axis1] = points[:, 0]
            data[:, axis2] = points[:, 1]
            z = self.predict(data)[0]
            plot_2D(points, z)
            plt.show()
        else:
            data = np.ones((n_points, dim))
            for d in range(dim):
                data[:, d] = self.best_point[d]
            data[:, axis1] = x


            z = self.predict(data)[0]

            plt.plot(x, z)
            plt.xlabel('Axis %i'%axis1)
            plt.ylabel('Result')
            plt.show()
