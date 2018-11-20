import tensorflow as tf
from sklearn.datasets import load_boston
from sklearn.preprocessing import scale
from matplotlib import pyplot as plt
import numpy as np
from scipy.optimize import minimize, differential_evolution, brute
import itertools
tf.logging.set_verbosity(tf.logging.WARN)

# 5 hidden layer multilayer perceptron model
# activation function: gaussian error linear unit
# adam algorithm for training
# thompson sampling of the ANN to pick next points
# bagging with 3 ANNs
# after sampling, the model is probed for minima with L-BFGS-B


# initially, train the SANN with a differential evolution algorithm biased towards exploration of 2N points
# afterwards, generate 3 predictions from the ANNs, then one from the DE
# feed these predictions to the experiment and sample new points to add to the training data
# repeat until minimum cost is determined

class NeuralNetwork():
    def __init__(self, parent, state, cost, bounds, params={'layers':10, 'neurons':64, 'optimizer':'adam', 'activation':'erf', 'initial_points':100, 'cycles':500, 'samples':1000, 'plot':0}, update = None):
        self.cost = cost
        self.parent = parent
        self.params = params
        self.bounds = bounds
        self.update = update
        hidden_units = np.ones(params['layers']) * params['neurons']
        optimizer = {'adam':tf.train.AdamOptimizer()}[params['optimizer']]
        activation_fn = {'erf':tf.erf}[params['activation']]
        self.state = state
        feature_cols = [tf.feature_column.numeric_column("x", shape=[len(state)])]
        self.estimator = tf.estimator.DNNRegressor(
                                        feature_columns=feature_cols,
                                        hidden_units=hidden_units,
                                        optimizer=optimizer,
                                        activation_fn=activation_fn
                                        )

        X, y, X_pred, y_pred = self.optimize(online = False)
        print('Converged to point',X_pred,'with cost',y_pred,'.')

    def get_input_fn(self, X, y, epochs = None, shuffle = True):
        return tf.estimator.inputs.numpy_input_fn(
            x={"x": X},
            y=y,
            num_epochs=epochs,
            shuffle=shuffle)

    def append(self, sample, X, y):
        ''' Appends a new sample to old observations'''
        sample = np.atleast_2d(sample)
        state = self.parent.array2state(sample[0], self.state)

        X = np.append(X, sample, axis=0)
        y = np.append(y, self.cost(state))

        return X, y

    def predict(self, X_pred):
        ''' Predicts the results over a vector X_pred '''
        X_pred = np.atleast_2d(X_pred)
        predictions = list(self.estimator.predict(input_fn=self.get_input_fn(X_pred, y=None, epochs = 1, shuffle = False)))
        y_pred = [x['predictions'][0] for x in predictions]
        if len(y_pred) > 1:
            return y_pred
        else:
            return -y_pred[0]

    def optimize(self, online = True):
        ''' Start by randomly sampling the parameter space '''
        X = np.array(np.random.uniform(self.bounds[:,0], self.bounds[:,1], size=(1,len(self.state))))
        state = self.parent.array2state(X[0], self.state)
        y = [self.cost(state)]
        for i in range(self.params['initial_points']):
            sample = np.random.uniform(self.bounds[:,0], self.bounds[:,1], size=(1,len(self.state)))
            X, y = self.append(sample, X, y)

        ''' Now iterate in closed loop '''
        for i in range(self.params['cycles']):
            if online:
                ''' Train model on data '''
                self.estimator.train(input_fn=self.get_input_fn(X,y), steps=10)
                X_new, y_pred = self.sample()
            else:
                X_new = np.random.uniform(self.bounds[:,0], self.bounds[:,1], size=(1,len(self.state)))

            X, y = self.append(X_new, X, y)
        self.estimator.train(input_fn=self.get_input_fn(X,y), max_steps=100)

        ''' Monte Carlo sampling of modeled cost surface to identify best point '''
        # X_pred, y_pred = self.sample()

        N = len(self.state)
        grid = []
        for n in range(N):
            space = np.linspace(self.bounds[n][0], self.bounds[n][1], int(np.sqrt(self.params['samples'])))
            grid.append(space)
        grid = np.array(grid)
        points = np.transpose(np.meshgrid(*[grid[n] for n in range(N)])).reshape(-1,N)
        costs = self.predict(points)

        y_pred = np.min(costs)
        X_pred = points[np.argmin(costs)]

        return X, y, X_pred, y_pred

    def sample(self):
        ''' Perform Monte Carlo sampling of the modeled cost surface to identify best point '''
        X_pred = np.random.uniform(self.bounds[:,0], self.bounds[:,1], size=(self.params['samples'],len(self.state)))
        y_pred = self.predict(X_pred)
        X_pred = X_pred[np.argmin(y_pred)]
        state = self.parent.array2state(X_pred, self.state)
        y_pred = self.cost(state)

        return X_pred, y_pred

    def plot(self, save = False):
        ''' Calculate the cost function over the predicted surface and plot. '''
        N = len(self.state)
        grid = []
        for n in range(N):
            space = np.linspace(self.bounds[n][0], self.bounds[n][1], 10)
            grid.append(space)
        grid = np.array(grid)
        points = np.transpose(np.meshgrid(*[grid[n] for n in range(N)])).reshape(-1,N)
        costs = self.predict(points)
        self.parent.plot_2D(points, costs, save)
