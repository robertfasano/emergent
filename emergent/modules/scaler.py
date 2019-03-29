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
        for thing in self.state:
            state[thing] = {}
            for knob in self.state[thing]:
                state[thing][knob] = arr[i]
                i += 1
        return state

    def state2array(self, state):
        ''' Converts a state dict into a numpy array. '''
        arr = np.array([])
        for thing in state:
            for knob in state[thing]:
                arr = np.append(arr, state[thing][knob])
        return arr

    def normalize(self, unnorm):
        ''' Normalizes a state or substate based on the bounds passed in at initialization. '''
        norm = {}

        for thing in unnorm:
            norm[thing] = {}
            for i in unnorm[thing]:
                min_val = self.limits[thing][i]['min']
                max_val = self.limits[thing][i]['max']
                norm[thing][i] = (unnorm[thing][i] - min_val)/(max_val-min_val)

        return norm

    def unnormalize(self, norm):
        ''' Converts normalized (0-1) state to physical state based on specified
            max and min parameter values. '''
        if isinstance(norm, np.ndarray):
            norm = self.array2state(norm)
        unnorm = {}
        for thing in norm:
            unnorm[thing] = {}
            for i in norm[thing]:
                min_val = self.limits[thing][i]['min']
                max_val = self.limits[thing][i]['max']
                unnorm[thing][i] = min_val + norm[thing][i] * (max_val-min_val)

        return unnorm
