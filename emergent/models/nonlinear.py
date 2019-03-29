from emergent.utilities.containers import Parameter
from emergent.utilities.decorators import algorithm
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, WhiteKernel
from scipy.optimize import minimize
from emergent.utilities.plotting import plot_2D
from emergent.models.model import Model
from scipy.optimize import curve_fit



class Nonlinear(Model):
    def __init__(self):
        super().__init__('Nonlinear')
        self.extension = None

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

    def fit(self, points=None, costs=None):
        if points is None:
            points = self.points
        if costs is None:
            costs = self.costs
        N = points.shape[1]
        p0 = tuple([0.5]*(2*N+1))
        self.popt, self.pcov = curve_fit(self.gaussian, points, costs, p0)

    def predict(self, X):
        return self.gaussian(X, *tuple(self.popt)), 0
