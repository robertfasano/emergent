from utility import Parameter, algorithm
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, WhiteKernel
from scipy.optimize import minimize
from emergent.archetypes import visualization

class GaussianProcessRegression():
    def __init__(self):
        ''' Define default parameters '''
        self.name = 'GaussianProcessRegression'
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
        self.params['Kernel amplitude'] = Parameter(name= 'Kernel amplitude',
                                            value = 1,
                                            min = 0,
                                            max = 10,
                                            description = 'Amplitude of modeled cost landscape')
        self.params['Kernel length scale'] = Parameter(name= 'Kernel length scale',
                                            value = 1,
                                            min = 0,
                                            max = 10,
                                            description = 'Characteristic size of cost landscape')
        self.params['Kernel noise'] = Parameter(name= 'Kernel noise',
                                            value = 0.1,
                                            min = 0,
                                            max = 10,
                                            description = 'Amplitude of modeled white noise process')

    def next_sample(self, X, b, cost, gaussian_process, restarts=25):
        ''' Generates the next sampling point by minimizing cost on the virtual
            response surface modeled by the Gaussian process. '''
        best_x = None
        best_acquisition_value = 999

        for starting_point in np.random.uniform(self.bounds[0][0], self.bounds[0][1], size=(restarts, X.shape[1])):
            res = minimize(fun=cost,
                       x0=starting_point.reshape(1, -1),
                       bounds=self.bounds,
                       method='L-BFGS-B',
                       args=(b, gaussian_process))
            if res.fun < best_acquisition_value:
                best_acquisition_value = res.fun
                best_x = res.x

        return best_x

    def effective_cost(self, x, b, gp):
        ''' Computes an effective cost for Gaussian process optimization, featuring
            some tradeoff between optimization and learning. '''
        ''' Watch for function recieveing a 2d x with higher dimensional state vectors (disagreement with internal GP dimension) '''
        mu, sigma = gp.predict(np.atleast_2d(x), return_std = True)
       # return (b*mu+np.sqrt(1-b**2)*sigma)
        return b*mu-(1-b)*sigma

    @algorithm
    def run(self, state, callback = None):
        ''' Online Gaussian process regression. Batch sampling is done with
            points with varying trade-off of optimization vs. exploration. '''
        if callback is None:
            callback = self.sampler.callback
        self.points, self.bounds = self.sampler.prepare(state)
        self.costs = np.array([self.sampler._cost(self.points)])
        X, c = self.sampler.sample(state, 'random_sampling', self.params['Presampled points'].value)
        self.points = np.append(np.atleast_2d(self.points), X, axis=0)
        self.costs = np.append(self.costs, c)
        kernel = C(self.params['Kernel amplitude'].value, (1e-3, 1e3)) * RBF(self.params['Kernel length scale'].value, (1e-2, 1e2)) + WhiteKernel(self.params['Kernel noise'].value)
        self.gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10)
        for i in range(int(self.params['Iterations'].value)):
            if not callback():
                return self.points[0:len(self.costs)], self.costs
            self.gp.fit(self.points,self.costs)
            a = i / (self.params['Iterations'].value-1)        # scale from explorer to optimizer through iterations
            for j in range(int(self.params['Batch size'].value)):
                b = a * j / (self.params['Batch size'].value-1)        # scale from explorer to optimizer throughout batch
                X_new = self.next_sample(self.points, b, self.effective_cost, self.gp, restarts=10)
                X_new = np.atleast_2d(X_new)
                self.points = np.append(self.points, X_new, axis=0)
                self.costs = np.append(self.costs, self.sampler._cost(self.points[-1]))
                self.progress = (j+i*self.params['Batch size'].value)/self.params['Batch size'].value/self.params['Iterations'].value
        best_point = self.sampler.array2state(self.points[np.argmin(self.costs)])
        self.sampler.actuate(self.sampler.unnormalize(best_point))

    def set_params(self, params):
        for p in params:
            self.params[p].value = params[p]

    def plot(self):
        ''' Predict and plot cost landscape '''
        grid = []
        N = self.points.shape[1]
        for n in range(N):
            space = np.linspace(self.bounds[n][0], self.bounds[n][1], 30)
            grid.append(space)
        grid = np.array(grid)
        predict_points = np.transpose(np.meshgrid(*[grid[n] for n in range(N)])).reshape(-1,N)
        predict_costs = np.array([])
        # for point in predict_points:
            # predict_costs = np.append(predict_costs, -self.gp.predict(np.atleast_2d(point)))
        predict_costs = -self.gp.predict(predict_points)
        return visualization.plot_2D(predict_points, predict_costs)
