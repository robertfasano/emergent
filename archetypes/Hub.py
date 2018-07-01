import sys
sys.path.append('C:\\Users\\Robbie\\Documents\\GitHub')
from PyQt5.QtCore import pyqtProperty, pyqtSlot
from labAPI.archetypes.Link import Link
from labAPI.archetypes.device import Device
from labAPI.archetypes.Optimizer import Optimizer
from labAPI.archetypes.Parallel import ProcessHandler
import numpy as np

class Hub(Device, Optimizer,Link, ProcessHandler):
    def __init__(self, engine, name):
        Device.__init__(self, name=name, lowlevel = False)
        Optimizer.__init__(self)
        Link.__init__(self, name = name, engine = engine)
        ProcessHandler.__init__(self)

        self.devices = []
        ''' Add devices here '''

    def _connect(self):
        for dev in self.devices:
            self.run_thread(target=dev._connect, stoppable = False)
#            dev._connect()

        self._params_to_state()

    def actuate(self, state):
        ''' Distribute state vector updates to appropriate devices '''
        for dev in self.devices:
            if len(dev.indices) > 0:
                substate = state[dev.indices]
                dev.actuate(substate)
        self.state = state

    def optimize(self, cost, axes, method, bounds, params):
        ''' Calls an Optimizer method to optimize the given cost function by
            actuating the given axes '''

        ''' The Optimizer has access to the Hub's self.actuate() method, and it
            will pass in states with only the target axes changed. '''
        self.run_optimization(cost, axes, method, bounds, params)

    def _params_to_state(self):
        ''' Prepare the state vector of the Device by parsing all state variables '''
        self.state = np.array([])
        self.state_names = np.array([])
        self.min = np.array([])
        self.max = np.array([])
        indices = np.array([])
        for device in self.params.keys():
            for param in self.params[device].keys():
                if self.params[device][param]['type'] == 'state':
                    self.state = np.append(self.state, self.params[device][param]['value'])
                    self.state_names = np.append(self.state_names, param)
                    self.max = np.append(self.max, self.params[device][param]['max'])
                    self.min = np.append(self.min, self.params[device][param]['min'])
                    indices = np.append(indices, self.params[device][param]['index'])

        sort_indices = np.argsort(indices)
        self.state = self.state[sort_indices]
        self.state_names = self.state_names[sort_indices]
        self.min = self.min[sort_indices]
        self.max = self.max[sort_indices]

    def _get_device(self, name):
        ''' Return a device handle given a str name '''
        for dev in self.devices:
            if dev.name == name:
                return dev
