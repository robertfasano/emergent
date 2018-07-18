import sys
sys.path.append('C:\\Users\\Robbie\\Documents\\GitHub')
from PyQt5.QtCore import pyqtProperty, pyqtSlot
from labAPI.archetypes.Link import Link
from labAPI.archetypes.device import Device
from labAPI.archetypes.Optimizer import Optimizer
from labAPI.archetypes.Parallel import ProcessHandler
import numpy as np

class Hub(Device, Optimizer,Link, ProcessHandler):
    ''' A module controlling multiple Devices and offering optimization,
        parallel process handling, and GUI communications. '''
    def __init__(self, engine, name):
        ''' Initializes the Hub and registers with a given name inside the
            QML engine. '''
        Device.__init__(self, name=name, lowlevel = False)
        self._params_to_state()

        Link.__init__(self, name = name, engine = engine)
        ProcessHandler.__init__(self)
        Optimizer.__init__(self)

        self.devices = []

    def _connect(self):
        ''' Attempts to connect to all child devices. '''
        for dev in self.devices:
            self._run_thread(target=dev._connect, stoppable = False)
#            dev._connect()

        self._params_to_state()

    def actuate(self, state, axes = None):
        ''' Distribute state vector updates to appropriate devices. '''
        if type(state) == list:
            state = np.array(state)
        assert type(state) == np.ndarray

        ''' If axes is not None, then we only want the actuation to affect
            certain axes. For each device dev, get the overlap of dev.indices
            with axes. Then, retrieve the current state and apply the update
            only along the overlap. '''
        for dev in self.devices:
            indices = dev.indices
            if axes != None:
                indices = np.array([x for x in axes if x in indices])
            if len(indices) > 0:
                target_state = dev.state
                if axes is None:
                    target_state[indices-dev.start_index] = state[indices]
                else:
                    target_state[indices-dev.start_index] = state[indices-dev.start_index]

                ''' Note: top line should be uncommented for Optimizer, but bottom line
                    for Application! Need to fix this disagreement! '''
                ''' The problem arises when we pass a state with no axes: I designed
                    this function to work with Optimizer with the upper line, which
                    assumes it will always receive substates. If the state is the total
                    state, it doesn't work. '''

                dev.actuate(target_state)
        if axes == None:
            self.state = state
        else:
            indices = [x for x in axes]
            self.state[indices] = state

    def optimize(self, cost, axes, method, bounds, params):
        ''' Calls an Optimizer method to optimize the given cost function by
            actuating the given axes. '''

        ''' The Optimizer has access to the Hub's self.actuate() method, and it
            will pass in states with only the target axes changed. '''
        self.run_optimization(cost, axes, method, bounds, params)

    def _params_to_state(self):
        ''' Prepare the state vector of the Device by parsing all state variables. '''
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
        ''' Return a device handle given a str name. '''
        for dev in self.devices:
            if dev.name == name:
                return dev
