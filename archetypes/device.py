''' The Device class handles persistent settings saved in json files in labAPI/settings. Settings are loaded into the
    Device.params dict and are handled differently based on their "type": "state" objects are loaded into a state vector
    to be made accessible by the Optimizer class, while "settings" objects (e.g. velocity of the a translation stage) are not.

    The settings file always contains the following attributes:
        id: the LabJack id, COM port, or similar address
        default: the default setpoint
'''
''' TODO: Add default setpoint '''
import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-2]))
import numpy as np
import json
import os

class Device():
    def __init__(self, name, base_path = None, lowlevel = True, parent = None):         # set parent to 0 instead of None just for the day
        ''' Instantiate a Device.
        Args:
            str name: a unique identifier for this device
            str base_path: an optional filepath
            bool lowlevel: if True, then this is a low-level device with its own params file
            Device parent: a higher-level Device incorporating this one     '''

        self.parent = parent
        self.name = name

        ''' Prepare filepath for parameter file '''
        if parent is not None:
            if base_path == None:
                base_path = os.path.realpath('')
            self.filename = base_path +'/settings/%s.txt'%self.name

#            with open(self.filename, 'r') as file:
#                self.id = json.load(file)['id']

        ''' Load a setpoint from parameter file '''
#        self.params = {'default': {}}
        self.params = {}
        self.setpoint = 'default'

        if lowlevel:
            self._load(self.setpoint)
            self._params_to_state()

        if parent is not None:
            self._update_parent()
            if hasattr(self.parent, 'devices'):
                self.parent.devices = np.append(self.parent.devices, self)
            else:
                self.parent.devices = np.array([self])

    def _actuate(self, state):
        if self.lowlevel == False:
            self.actuate(state)

    def actuate(self, state):
        ''' Ensures that the target state is within bounds, then calls the
            device-specific actuate() method to update the physical state.
            Finally, updates the internal state and params '''
        state = np.clip(state, self.min, self.max)
        self._actuate(state)
        self.state = state
        self._state_to_params()

    def _save(self, setpoint=None):
        ''' Read in setpoints from file, append or update current setpoint, and write '''
        if setpoint is None:
            setpoint = self.setpoint
        with open(self.filename, 'r') as file:
            setpoints = json.load(file)
        setpoints[setpoint] = self.params
        with open(self.filename, 'w') as file:
            json.dump(setpoints,file)

    def _load(self, setpoint):
        ''' Read in setpoints from file '''
        with open(self.filename, 'r') as file:
            self.params = json.load(file)[setpoint]
        if self.parent is not None:
            self.parent.params[self.name] = self.params

    def _delete(self, setpoint):
        ''' Read in setpoints from file, delete target setpoint, and write '''
        if self.parent is None:
            with open(self.filename, 'r') as file:
                setpoints = json.load(file)
            del setpoints[setpoint]
            with open(self.filename, 'w') as file:
                json.dump(setpoints,file)
        else:
            print('Only top-level devices can delete setpoints.')

    def _params_to_state(self):
        ''' Prepare the normalized state vector of the Device by parsing all state variables '''
        self.state = np.array([])
        self.min = np.array([])
        self.max = np.array([])
        self.indices = np.array([])
        for s in self.params.keys():
            if self.params[s]['type'] == 'state':
                self.state = np.append(self.state, self.params[s]['value'])
                self.max = np.append(self.max, self.params[s]['max'])
                self.min = np.append(self.min, self.params[s]['min'])
                self.indices = np.append(self.indices, self.params[s]['index'])
        sorted_indices = np.argsort(self.indices)
        for x in [self.indices, self.state, self.min, self.max]:
            x = x[sorted_indices]
        self.indices = self.indices.astype(int)
        if len(self.indices) > 0:
            self.start_index = np.min(self.indices)

    def _state_to_params(self):
        ''' Update the params file with the current values of the state vector '''
        for s in self.params.keys():
            if self.params[s]['type'] == 'state':
                self.params[s]['value'] = self.state[self.params[s]['index']-self.start_index]
                state = self.state[self.params[s]['index']-self.start_index]
                self.params[s]['value'] = state
        self._save(self.setpoint)
        if self.parent is not None:
            self._update_parent

    def _update_parent(self):
        ''' Push current params upstream to parent '''
        self.parent.params[self.name] = self.params

    def _get_param_by_index(self, index):
        for s in self.params.keys():
            try:
                if self.params[s]['index'] == index:
                    return s
            except:
                pass

    def _get_index_by_param(self, param):
        try:
            return self.params[param]['index']
        except KeyError:
            return None

    def _list_methods(self):
        methods = [func for func in dir(self) if callable(getattr(self, func)) and not func.startswith("__")]
        print(methods)

if __name__ == '__main__':
    d = Device('device')
    d._load('setpoint1')
    d._save('setpoint2')
    d._delete('setpoint2')
    d._params_to_state()
    d._state[0] = 137
    d._state_to_params()
    d._save('setpoint1')
