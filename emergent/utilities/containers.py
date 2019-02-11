''' The State class offers several convenient features for state representation over
    a simple dict:

    * Substates including only specified indices can be obtained through State.get()
    * State.copy() returns a detached clone of the original State (rather than creating a reference as with a dict)
    * Multiple inputs can be updated with one call to the State.update() method
    * The ordering in which objects are added to the State is preserved, so that State instances can be converted to and from numpy arrays without scrambling the inputs.
'''
from copy import deepcopy
from collections import OrderedDict

class State(OrderedDict):
    def __init__(self):
        return

    def get(self, keys):
        ''' Returns a substate based on the given keys. For example, let self={'a':{'x':1,'y':2}, 'b':{'z':3}}.
            Calling self.get(['a']) returns {'a':{'x':1, 'y':2}}, while calling self.get('{'a':['x']') returns
            only {'a':{'x':1}}. '''
        state = {}
        if type(keys) is list:
            for thing in keys:
                state[thing] = self[thing]
        elif type(keys) is dict:
            for thing in keys:
                print(thing)
                state[thing] = {}
                for input in keys[thing]:
                    print(input)
                    state[thing][input] = self[thing][input]
        return state

    def update(self, state):
        ''' Returns a state dict formed by updating self with the passed state. '''
        new_state = self.copy()
        for thing in state:
            if type(state[thing]) is dict:        # then this is a (nested) hub state
                for input in state[thing]:
                    new_state[thing][input] = state[thing][input]
            else:                               # this is a thing state
                new_state[thing] = state[thing]
        return new_state

    def copy(self):
        return deepcopy(self)

    def get_fullnames(self):
        fullnames = []
        for thing in self:
            for input in self[thing]:
                fullnames.append(thing+': '+input)
        return fullnames

class Parameter():
    def __init__(self, name, value, min = None, max = None, description = ''):
        self.name = name
        self.value = value
        self.min = min
        self.max = max
        self.description = description

        
if __name__ == '__main__':
    s = State()
    s['a'] = 1
    s['b'] = 2
    s['c'] = 3

    t = State()
    t['a'] = {'x':1, 'y':2}
    t['b'] = {'z':3}