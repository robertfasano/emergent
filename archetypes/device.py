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
                base_path = os.path.realpath('..')
            self.filename = base_path +'/settings/%s.txt'%self.name
            
            with open(self.filename, 'r') as file:
                self.id = json.load(file)['id']
        
        ''' Load a setpoint from parameter file '''
#        self.params = {'default': {}}
        self.params = {}
        self.setpoint = 'default'
        
        if lowlevel:
            self.load(self.setpoint)
            self.params_to_state()
            
        if parent is not None:
            self.update_parent()
            if hasattr(self.parent, 'devices'):
                self.parent.devices.append(self)
            else:
                self.parent.devices = [self]

#        with open(self.filename, 'r') as file:
#            self.id = json.load(file)['id']
        
        
    def actuate(self, state):
        ''' Change the internal state to a specified state and update self.params accordingly '''
        self.state = state
        self.state_to_params()
        
    def save(self, setpoint):           
        ''' Read in setpoints from file, append or update current setpoint, and write '''
        with open(self.filename, 'r') as file:
            setpoints = json.load(file)
        setpoints[setpoint] = self.params
        with open(self.filename, 'w') as file:
            json.dump(setpoints,file)
            
    def load(self, setpoint):   # need to uncomment when parent integration is complete
        ''' Read in setpoints from file '''
        with open(self.filename, 'r') as file:
            self.params = json.load(file)[setpoint]
        if self.parent is not None:
            self.parent.params[self.name] = self.params
            
    def delete(self, setpoint):         
        ''' Read in setpoints from file, delete target setpoint, and write '''
        if self.parent is None:
            with open(self.filename, 'r') as file:
                setpoints = json.load(file)
            del setpoints[setpoint]
            with open(self.filename, 'w') as file:
                json.dump(setpoints,file)    
        else:
            print('Only top-level devices can delete setpoints.')
            
    def params_to_state(self):
        ''' Prepare the normalized state vector of the Device by parsing all state variables '''
        self.state = np.array([])
        self.min = np.array([])
        self.max = np.array([])
        indices = np.array([])
        for s in self.params.keys():
            if self.params[s]['type'] == 'state':
                self.state = np.append(self.state, self.params[s]['value'])
                self.max = np.append(self.max, self.params[s]['max'])
                self.min = np.append(self.min, self.params[s]['min'])
                indices = np.append(indices, self.params[s]['index'])
                
        self.state = self.state[np.argsort(indices)]
        self.min = self.min[np.argsort(indices)]
        self.max = self.max[np.argsort(indices)]
        
#        self.state = (self.state-self.min)/(self.max-self.min)      # normalize
        
    def state_to_params(self):
        ''' Update the params file with the current values of the state vector '''
        for s in self.params.keys():
            if self.params[s]['type'] == 'state':
                self.params[s]['value'] = self.state[self.params[s]['index']]          
                state = self.state[self.params[s]['index']]
#                state = self.min + state*(self.max-self.min)         # unnormalize
                self.params[s]['value'] = state
        self.save(self.setpoint)
        
    def update_parent(self):
        ''' Push current params upstream to parent '''
        self.parent.params[self.name] = self.params

    def get_param_by_index(self, index):
        for s in self.params.keys():
            try:
                if self.params[s]['index'] == index:
                    return s
            except:
                pass
            
    def get_index_by_param(self, param):
        try:
            return self.params[param]['index']
        except KeyError:
            return None
            
if __name__ == '__main__':
    d = Device('device')
    d.load('setpoint1')
    d.save('setpoint2')
    d.delete('setpoint2')
    d.params_to_state()
    d.state[0] = 137
    d.state_to_params()
    d.save('setpoint1')

    