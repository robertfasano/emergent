import numpy as np

class Scaler_dev():
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

    def normalize(self, unnorm):
        ''' Normalizes a state or substate based on the bounds passed in at initialization. '''
        norm = {}

        for var in unnorm:
            min_val = self.limits[var]['min']
            max_val = self.limits[var]['max']
            norm[var] = (unnorm[var] - min_val)/(max_val-min_val)

        return norm

    def unnormalize(self, norm, array=False):
        ''' Converts normalized (0-1) state to physical state based on specified
            max and min parameter values. '''
        if isinstance(norm, np.ndarray):
            norm = self.array2state(norm)
        unnorm = {}
        for var in norm:
            min_val = self.limits[var]['min']
            max_val = self.limits[var]['max']
            unnorm[var] = min_val + norm[var] * (max_val-min_val)
        if array:
            return self.state2array(unnorm)
        return unnorm
