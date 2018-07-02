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

''' Experimental parameters '''
d = 5      # number of dimensions
N = 2*d      # number of initial points
iterations = 10
bounds = np.array(list(itertools.repeat([-1,1], d)))

''' Cost function parameters '''
SNR = 20    # noise parameter

''' Learning parameters '''
layers = 5
neurons = 64
hidden_units = np.ones(layers) * neurons
optimizer = tf.train.AdamOptimizer()
activation_fn = tf.erf

def cost(X, noise=1/SNR):
    ''' A gaussian cost function in N dimensions. Overload in child classes with appropriate function '''
    cost = 1
    sigma = 1/3

    point = np.atleast_2d(X)
    for n in range(point.shape[1]):
        cost *= np.exp(-point[:,n]**2/(2*sigma**2))
    cost += np.random.normal(0,noise)

    return -cost

''' Declare estimator '''
feature_cols = [tf.feature_column.numeric_column("x", shape=[d])]
estimator = tf.estimator.DNNRegressor(
    feature_columns=feature_cols,
    hidden_units=hidden_units,
    optimizer=optimizer,
    activation_fn=activation_fn
    )

''' Sample initial N points '''

def get_input_fn(X, y, epochs = None, shuffle = True):
    return tf.estimator.inputs.numpy_input_fn(
        x={"x": X},
        y=y,
        num_epochs=epochs,
        shuffle=shuffle)

def append(sample, X, y, cost, noise):
    ''' Appends a new sample to old observations'''
    sample = np.atleast_2d(sample)
    X = np.append(X, sample, axis=0)
    y = np.append(y, cost(sample, noise))

    return X, y

def predict(X_pred):
    ''' Predicts the results over a vector X_pred '''
#    X_pred = np.atleast_2d(X_pred)
    predictions = list(estimator.predict(input_fn=get_input_fn(X_pred, y=None, epochs = 1, shuffle = False)))
    y_pred = [x['predictions'][0] for x in predictions]
    if len(y_pred) > 1:
        return y_pred
    else:
        return -y_pred[0]


''' Optimization loop '''
def optimize(cycles = 10, online = True):
    ''' Start by randomly sampling the parameter space '''
    X = np.array(np.random.uniform(bounds[:,0], bounds[:,1], size=(1,d)))
    y = [cost(X,noise = 1/SNR)]
    for i in range(N):
        sample = np.random.uniform(bounds[:,0], bounds[:,1], size=(1,d))
        X, y = append(sample, X, y, cost=cost, noise = 1/SNR)

    ''' Now iterate in closed loop '''
    for i in range(cycles):
        if online:
            ''' Train model on data '''
            estimator.train(input_fn=get_input_fn(X,y), steps=10)
            X_new = differential_evolution(predict, bounds).x
#            X_new = brute(predict, bounds).x

        else:
            X_new = np.random.uniform(bounds[:,0], bounds[:,1], size=(1,d))

        X, y = append(X_new, X, y, cost=cost, noise = 1/SNR)
        print(i)
    estimator.train(input_fn=get_input_fn(X,y), max_steps=100)

    ''' Search for optimal point through grid search '''
#     grid = []
#     for n in range(X.shape[1]):
#         space = np.linspace(bounds[n][0], bounds[n][1], 100)
# #            space = np.linspace(X[-1]-span/2, X[-1]+span/2, 25)
#
#         grid.append(space)
#     grid = np.array(grid)
#     points = np.transpose(np.meshgrid(*[grid[n] for n in range(X.shape[1])])).reshape(-1,X.shape[1])
#
#     y_pred = predict(points)
#     X_pred = np.atleast_2d(points[np.argmax(y_pred)])
#     y_pred = np.max(y_pred)

    X_pred= differential_evolution(predict, bounds).x
#    X_pred= brute(predict, bounds).x

    y_pred = predict(X_pred)


    return X, y, X_pred, y_pred

X, y, X_pred, y_pred = optimize(cycles = 25, online = False)
plt.plot(X,y, '.')
plt.plot(X_pred,y_pred, 'o')


X_fit = np.linspace(-1, 1, 100)
y_fit = predict(X_fit)
plt.plot(X_fit, y_fit)


