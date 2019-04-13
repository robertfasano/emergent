import numpy as np

class Scaler():
    ''' General methods '''
    def __init__(self, state, limits):
        self.state = state
        self.limits = limits

    ''' State conversion functions '''
    def array2state(self, arr):
        ''' Converts a numpy array into a state dict with keys matching self.state. '''
        state = {}
        i = 0
        for var in self.state:
            state[var] = arr[i]
            i += 1
        return state

    def state2array(self, state):
        ''' Converts a state dict into a numpy array. '''
        arr = np.array([])
        for var in state:
            arr = np.append(arr, state[var])
        return arr

    def normalize(self, state, bounds=None, norm = {}):
        ''' Recursively normalizes a dictionary with arbitrary nesting
            matching the passed bounds dict. '''
        if bounds is None:
            bounds = self.limits
        for key in state:
            if not isinstance(state[key], dict):
                norm[key] = (state[key] - bounds[key][0])/(bounds[key][1]-bounds[key][0])
            else:
                norm[key] = {}
                normalize(state[key], bounds[key], norm[key])
        return norm

    def unnormalize(self, state, bounds=None, unnorm = {}):
        if bounds is None:
            bounds = self.limits
        for key in state:
            if not isinstance(state[key], dict):
                unnorm[key] = bounds[key][0] + state[key] * (bounds[key][1]-bounds[key][0])
            else:
                unnorm[key] = {}
                unnormalize(state[key], bounds[key], unnorm[key])
        return unnorm
