import numpy as np
from copy import deepcopy

class Scaler():
    ''' General methods '''
    def __init__(self, state, limits):
        self.state = state
        self.limits = limits

    ''' State conversion functions '''
    def array2state(self, arr, protostate=None, state=None, i=0):
        ''' Converts a state dict into a numpy array. '''
        if i == 0:
            self.i = 0
        if state is None:
            state = {}
        if protostate is None:
            protostate = deepcopy(self.state)
        for key in protostate:
            if isinstance(protostate[key], dict):
                state[key] = {}
                state[key] = self.array2state(arr, protostate[key], state[key], self.i)
            else:
                state[key] = arr[self.i]
                self.i += 1
        return deepcopy(state)

    def state2array(self, state, arr=np.array([])):
        ''' Converts a state dict into a numpy array. '''
        for key in state:
            if isinstance(state[key], dict):
                arr = self.state2array(state[key], arr)
            else:
                arr = np.append(arr, state[key])

        return arr

    def normalize(self, state, bounds=None, norm = None):
        ''' Recursively normalizes a dictionary with arbitrary nesting
            matching the passed bounds dict. '''
        if norm is None:
            norm = {}
        if bounds is None:
            bounds = self.limits
        for key in state:
            if not isinstance(state[key], dict):
                norm[key] = (state[key] - bounds[key][0])/(bounds[key][1]-bounds[key][0])
            else:
                norm[key] = {}
                self.normalize(state[key], bounds[key], norm[key])
        return norm

    def unnormalize(self, state, bounds=None, unnorm = None):
        if unnorm is None:
            unnorm = {}
        if bounds is None:
            bounds = self.limits
        for key in state:
            if not isinstance(state[key], dict):
                unnorm[key] = bounds[key][0] + state[key] * (bounds[key][1]-bounds[key][0])
            else:
                unnorm[key] = {}
                self.unnormalize(state[key], bounds[key], unnorm[key])
        return unnorm
