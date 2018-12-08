from utility import Parameter, algorithm
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, WhiteKernel
from scipy.optimize import minimize

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

    def next_sample(self, X, bounds, b, cost, gaussian_process, restarts=25):
        ''' Generates the next sampling point by minimizing cost on the virtual
            response surface modeled by the Gaussian process. '''
        best_x = None
        best_acquisition_value = 999

        for starting_point in np.random.uniform(bounds[0][0], bounds[0][1], size=(restarts, X.shape[1])):
            res = minimize(fun=cost,
                       x0=starting_point.reshape(1, -1),
                       bounds=bounds,
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
    def run(self, state, cost, params={'Presampled points': 15, 'Iterations':10, 'Batch size':10, 'Kernel amplitude': 1, 'Kernel length scale': 1, 'Kernel noise': 0.1}, cost_params = {}, callback = None):
        ''' Online Gaussian process regression. Batch sampling is done with
            points with varying trade-off of optimization vs. exploration. '''
        if callback is None:
            callback = self.sampler.callback
        X, bounds = self.sampler.initialize(state, cost, params, cost_params)
        c = np.array([self.sampler._cost(X)])
        points, costs = self.sampler.sample(state, cost, cost_params, 'random_sampling', params['Presampled points'])
        X = np.append(np.atleast_2d(X), points, axis=0)
        c = np.append(c, costs)
        kernel = C(params['Kernel amplitude'], (1e-3, 1e3)) * RBF(params['Kernel length scale'], (1e-2, 1e2)) + WhiteKernel(params['Kernel noise'])
        self.gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10)
        for i in range(int(params['Iterations'])):
            if not callback():
                return points[0:len(costs)], costs
            self.gp.fit(X,c)
            a = i / (params['Iterations']-1)        # scale from explorer to optimizer through iterations
            for j in range(int(params['Batch size'])):
                b = a * j / (params['Batch size']-1)        # scale from explorer to optimizer throughout batch
                X_new = self.next_sample(X, bounds, b, self.effective_cost, self.gp, restarts=10)
                X_new = np.atleast_2d(X_new)
                X = np.append(X, X_new, axis=0)
                c = np.append(c, self.sampler._cost(X[-1]))
                self.progress = (j+i*params['Batch size'])/params['Batch size']/params['Iterations']
        best_point = self.sampler.array2state(X[np.argmin(c)])
        self.sampler.actuate(self.sampler.unnormalize(best_point))
        # if params['plot']:
        #     self.plot_optimization(lbl = 'Gaussian Processing')     # plot trajectory
        #     ''' Predict and plot cost landscape '''
        #     grid = []
        #     N = X.shape[1]
        #     for n in range(N):
        #         space = np.linspace(bounds[n][0], bounds[n][1], 30)
        #         grid.append(space)
        #     grid = np.array(grid)
        #     predict_points = np.transpose(np.meshgrid(*[grid[n] for n in range(N)])).reshape(-1,N)
        #     predict_costs = np.array([])
        #     for point in predict_points:
        #         predict_costs = np.append(predict_costs, self.gp.predict(np.atleast_2d(point)))
        #     plot_2D(predict_points, predict_costs)
        return X, c
