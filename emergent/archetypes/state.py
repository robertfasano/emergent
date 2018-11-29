from copy import deepcopy

class State(dict):
    def __init__(self):
        return
    
    def get(self, keys):
        ''' Returns a substate based on the given keys. For example, let self={'a':{'x':1,'y':2}, 'b':{'z':3}}.
            Calling self.get(['a']) returns {'a':{'x':1, 'y':2}}, while calling self.get('{'a':['x']') returns
            only {'a':{'x':1}}. '''
        state = {}
        if type(keys) is list:
            for dev in keys:
                state[dev] = self[dev]
        elif type(keys) is dict:
            for dev in keys:
                print(dev)
                state[dev] = {}
                for input in keys[dev]:
                    print(input)
                    state[dev][input] = self[dev][input]
        return state
    
    def update(self, state):
        ''' Returns a state dict formed by updating self with the passed state. '''
        new_state = self.copy()
        for dev in state:
            if type(state[dev]) is dict:        # then this is a (nested) hub state
                for input in state[dev]:
                    new_state[dev][input] = state[dev][input]
            else:                               # this is a device state
                new_state[dev] = state[dev]
        return new_state
        
    def copy(self):
        return deepcopy(self)
    

  
    
if __name__ == '__main__':
    s = State()
    s['a'] = 1
    s['b'] = 2
    s['c'] = 3
    
    t = State()
    t['a'] = {'x':1, 'y':2}
    t['b'] = {'z':3}
