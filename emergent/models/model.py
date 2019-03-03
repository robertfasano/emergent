import numpy as np
from scipy.optimize import minimize
from emergent.utilities.plotting import plot_2D
from emergent.utilities.containers import Parameter


class Model():
    def __init__(self, name=None):
        self.name = name
        self.params = {}
        self.params['Leash'] = Parameter(name= 'Leash',
                                            value = 0.25,
                                            min = 0.01,
                                            max = 0.25,
                                            description = 'Allowed search range relative to last best point')

    def append(self, point, cost):
        self.points = np.append(np.atleast_2d(self.points), np.atleast_2d(point), axis=0)
        self.costs = np.append(self.costs, cost)

    def effective_cost(self, X, b):
        ''' Computes an effective cost, featuring
            some tradeoff between optimization and learning. '''
        mu, sigma = self.predict(X)
       # return (b*mu+np.sqrt(1-b**2)*sigma)
        return b*mu-(1-b)*sigma

    def fit(self):
        ''' Override for a given model with the specific fitting method used. '''
        return

    def minimum(self):
        return self.next_sample(1)

    def next_sample(self, b, restarts=25):
        ''' Generates the next sampling point by minimizing cost on the virtual
            response surface. '''
        X = self.points
        best_x = None
        best_acquisition_value = 999
        best_point = self.points[np.argmin(self.costs)]
        leash = self.params['Leash'].value * (self.bounds[0][1] - self.bounds[0][0])

        ''' Form random vector within allowed range of last best point '''
        x0 = np.zeros((X.shape[1], restarts))
        leashed_bounds = []
        for i in range(X.shape[1]):
            xmin = np.max([best_point[i] - leash, self.bounds[i][0]])
            xmax = np.min([best_point[i] + leash, self.bounds[i][1]])
            leashed_bounds.append([xmin, xmax])
            x0[i] =  np.random.uniform(xmin, xmax, restarts)
        x0 = x0.T
        for starting_point in x0:
            res = minimize(fun=self.effective_cost,
                       x0=starting_point.reshape(1, -1),
                       bounds=leashed_bounds,
                       method='L-BFGS-B',
                       args=(b,))
            if res.fun < best_acquisition_value:
                best_acquisition_value = res.fun
                best_x = res.x

        return best_x

    def predict(self, state):
        ''' Override for a given model with the specific prediction method used. '''
        return

    def prepare(self, sampler):
        self.sampler = sampler
        self.points, self.bounds = self.sampler.prepare(sampler.state)
        self.costs = np.array([self.sampler._cost(self.points)])

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
        predict_costs, predict_uncertainties = self.predict(predict_points)
        predict_costs *= -1

        return plot_2D(predict_points, predict_costs, limits=self.sampler.get_limits())
