''' The State class offers several convenient features for state representation over
    a simple dict:

    * Substates including only specified indices can be obtained through State.get()
    * State.copy() returns a detached clone of the original State (rather than creating a reference as with a dict)
    * Multiple knobs can be updated with one call to the State.update() method
    * The ordering in which objects are added to the State is preserved, so that State instances can be converted to and from numpy arrays without scrambling the knobs.
'''
from copy import deepcopy
from collections import OrderedDict, Mapping

class DataDict(OrderedDict):
    def as_dict(self):
        d = {}
        for key in self:
            d[key] = self[key]
        return d

    def patch(self, new, old=None):
        ''' Updates any nested elements common to both dicts, but does NOT
            create new elements. '''
        if old is None:
            old = self
        for k, v in new.items():
            if isinstance(v, Mapping):
                if k in old:
                    old[k] = self.patch(v, old.get(k, {}))
            else:
                if k in old:
                    old[k] = v
        return old

    def put(self, new, old=None):
        ''' Updates any nested elements common to both dicts, and additionally creates new elements. '''
        if old is None:
            old = self
        for k, v in new.items():
            if isinstance(v, Mapping):
                old[k] = self.put(v, old.get(k, {}))
            else:
                old[k] = v
        return old

    def copy(self):
        return deepcopy(self)

    def find(self, field, label = True):
        ''' Calling reduce_pass will remove all endpoints not in field,
            but will leave empty dicts. We need to do one additional pass
            per level of nesting. May lead to unexpected behavior
            if keys are repeated across nested levels! '''
        self.nest_level = 0
        d = self._find_pass(field, self.copy())
        for i in range(self.nest_level-1):
            d = self._find_pass(field, d)

        if not label:
            d = self._unredundify(field, d)
        return d

    def _find_pass(self, field, d):
        ''' Returns the original dict with all endpoints except
        the field string removed '''
        for key in list(d.keys()):
            if type(d[key]) in [dict, self.__class__]:
                if len(d[key]) == 0:
                    del d[key]
                else:
                    self.nest_level += 1
                    self._find_pass(field, d[key])
            else:
                if key != field:
                    del d[key]
        return d

    def _unredundify(self, field, d):
        ''' Pass a dict where all endpoints have the same key.
            Returns the same dict with the key removed and
            d[key] replacing d. May lead to unexpected behavior
            if keys are repeated across nested levels!'''
        if hasattr(d, 'keys'):
            for key in list(d.keys()):
                if key == field:
                    d=d[key]
                    break
                else:
                    new = self._unredundify(field, d[key])
                    if type(new) not in [dict, self.__class__]:
                        d[key] = new
        return d

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
                for knob in keys[thing]:
                    print(knob)
                    state[thing][knob] = self[thing][knob]
        return state

    def update(self, state):
        ''' Returns a state dict formed by updating self with the passed state. '''
        new_state = self.copy()
        for thing in state:
            if type(state[thing]) is dict:        # then this is a (nested) hub state
                for knob in state[thing]:
                    new_state[thing][knob] = state[thing][knob]
            else:                               # this is a thing state
                new_state[thing] = state[thing]
        return new_state

    def copy(self):
        return deepcopy(self)

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
