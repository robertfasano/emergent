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
        for device in self.state:
            state[device] = {}
            for knob in self.state[device]:
                state[device][knob] = arr[i]
                i += 1
        return state

    def state2array(self, state):
        ''' Converts a state dict into a numpy array. '''
        arr = np.array([])
        for device in state:
            for knob in state[device]:
                arr = np.append(arr, state[device][knob])
        return arr

    def normalize(self, unnorm):
        ''' Normalizes a state or substate based on the bounds passed in at initialization. '''
        norm = {}

        for device in unnorm:
            norm[device] = {}
            for i in unnorm[device]:
                min_val = self.limits[device][i]['min']
                max_val = self.limits[device][i]['max']
                norm[device][i] = (unnorm[device][i] - min_val)/(max_val-min_val)

        return norm

    def unnormalize(self, norm):
        ''' Converts normalized (0-1) state to physical state based on specified
            max and min parameter values. '''
        if isinstance(norm, np.ndarray):
            norm = self.array2state(norm)
        unnorm = {}
        for device in norm:
            unnorm[device] = {}
            for i in norm[device]:
                min_val = self.limits[device][i]['min']
                max_val = self.limits[device][i]['max']
                unnorm[device][i] = min_val + norm[device][i] * (max_val-min_val)

        return unnorm
