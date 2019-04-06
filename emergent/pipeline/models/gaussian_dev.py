from scipy.optimize import curve_fit
import numpy as np
from emergent.pipeline.models.model import Model

class GaussianModel(Model):
    def __init__(self):
        super().__init__()

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
        ''' Return a cost and uncertainty estimate at a point X. '''
        return self.gaussian(X, *tuple(self.popt)), 0

    def measure(self, X):
        ''' Return a cost estimate at a point X '''
        return self.predict(X)[0][0]
