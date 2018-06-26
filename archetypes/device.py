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
from threading import Timer

class Device():
    def __init__(self, name):
        self.name = name
        self.params = {}
        self.filename = os.path.realpath('..')+'/settings/%s.txt'%self.name
        
        with open(self.filename, 'r') as file:
            self.id = json.load(file)['id']
        
        self.setpoint = 'default'
        self.load(self.setpoint)
        self.params_to_state()
        
        self.toggle = 0
        
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
            
    def load(self, setpoint):
        ''' Read in setpoints from file '''
        with open(self.filename, 'r') as file:
            self.params = json.load(file)[setpoint]
    
    def delete(self, setpoint):
        ''' Read in setpoints from file, delete target setpoint, and write '''
        with open(self.filename, 'r') as file:
            setpoints = json.load(file)
        del setpoints[setpoint]
        with open(self.filename, 'w') as file:
            json.dump(setpoints,file)    
            
    def params_to_state(self):
        ''' Prepare the state vector of the Device by parsing all state variables '''
        self.state = np.array([])
        indices = np.array([])
        for s in self.params.keys():
            if self.params[s]['type'] == 'state':
                self.state = np.append(self.state, self.params[s]['value'])
                indices = np.append(indices, self.params[s]['index'])
        self.state = self.state[np.argsort(indices)]
        
    def state_to_params(self):
        ''' Update the params file with the current values of the state vector '''
        for s in self.params.keys():
            if self.params[s]['type'] == 'state':
                self.params[s]['value'] = self.state[self.params[s]['index']]
        self.save(self.setpoint)
        
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
        
    def square_wave(self, period):
        ''' Generates a square wave with specified period. Currently only works for 1D state devices '''
        Timer(period/2, self.square_wave).start()
        self.toggle = (self.toggle+1)%2
        ''' Move between max and min '''
        if self.toggle:
            self.actuate([self.max])
        else:
            self.actuate([self.min])
            
if __name__ == '__main__':
    d = Device('device')
    d.load('setpoint1')
    d.save('setpoint2')
    d.delete('setpoint2')
    d.params_to_state()
    d.state[0] = 137
    d.state_to_params()
    d.save('setpoint1')

    