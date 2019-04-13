from emergent.utilities.containers import Parameter
from emergent.utilities.decorators import algorithm
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, WhiteKernel
from scipy.optimize import minimize
from emergent.pipeline.plotting import plot_1D, plot_2D

from scipy.optimize import curve_fit
from emergent.pipeline import Block
import matplotlib.pyplot as plt

class GaussianModel(Block):
    def __init__(self, params = {}):
        super().__init__()
        self.params = {}
        self.params['Optimizer'] = Parameter(name='Optimizer', value=self.list_optimizers(), type=str)
        for p in params:
            self.params[p].value = params[p]
            if p == 'Optimizer':
                self.optimizer = params['Optimizer']
                self.optimizer.measure = self.measure

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
        print('measure model')
        return self.predict(X)[0][0]

    def run(self, points, costs, bounds=None):
        ''' Trains on the passed data, numerically optimizes the modeled response
            surface, then makes a physical measurement at the modeled minimum. '''
        self.fit(points, costs)
        # if hasattr(self, 'optimizer'):
        x_pred, y_pred = self.optimizer.run(points.copy(), costs.copy(), bounds)
        x_pred = x_pred[len(points)::]
        y_pred = y_pred[len(costs)::]
        point = x_pred[np.argmin(y_pred)]
        self.best_point, best_cost = point, np.array([self.pipeline.measure(point)])
        # else:
        #     self.best_point = np.array([self.popt[1], self.popt[2]])
        #     best_cost = np.array([self.pipeline.measure(self.best_point)])
        points = np.append(points, np.atleast_2d(self.best_point), axis=0)
        costs = np.append(costs, best_cost)

        return points, costs

    def list_optimizers(self):
        import importlib, inspect
        module = importlib.import_module('emergent.pipeline.optimizers')
        names = []
        for a in dir(module):
            if '__' not in a:
                inst = getattr(module, a)
                if inspect.isclass(inst):
                    names.append(inst.__name__)
        return names

    def plot(self, axis1, axis2=None, n_points = 30, mode='cross-section'):
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
            data = self.pipeline.unnormalize(data)
            points = data[:, [axis1, axis2]]
            plot_2D(points, z, mode=mode)
            plt.show()
        else:
            data = np.ones((n_points, dim))
            for d in range(dim):
                data[:, d] = self.best_point[d]
            data[:, axis1] = x


            z = self.predict(data)[0]
            x = self.pipeline.unnormalize(data)[:, axis1]
            plt.plot(x, z)
            plt.xlabel('Axis %i'%axis1)
            plt.ylabel('Result')
            plt.show()
