'''
    A Hub is an object which controls one or more Devices to regulate the outcome
    of an experiment. For example, for beam alignment into an optical fiber we would
    require one or more Devices for mirror control, as well as a Hub which measures
    the transmitted power and coordinates commands to its connected Devices to maximize
    the signal. The Hub class also contains methods for saving and loading states
    to/from file, for monitoring important variables through the Watchdog framework,
    and for optimizing itself by interfacing with other modules.
'''
import json
import logging as log
from emergent.utilities.containers import DataDict
from emergent.core import Node
from emergent.utilities.persistence import __getstate__

class Hub(Node):
    ''' The Hub oversees connected Devices, allowing the Knobs to be
        algorithmically tuned to optimize some target function. '''

    def __init__(self, name, params={}, core=None):
        """Initializes a Hub.

        Args:
            name (str): node name. All Hubs should have unique names.
        """
        self.params = params
        self._name_ = name      # save hardcoded name as private variable
        ''' Update self.params with any parameters associated with the Network '''
        try:
            core_params = core.params[name]
        except KeyError:
            core.params[name] = {}
            core_params = {}
        for p in core_params:
            self.params[p] = core_params[p]
        if 'name' in core_params:
            name = core_params['name']
        self.core = core
        self.name = name

        super().__init__(name, None)
        self.devices = {}
        self.state = DataDict()
        self.range = DataDict()
        self.samplers = {}
        self.node_type = 'hub'
        self.ignored = []
        self.__getstate__ = lambda: __getstate__(['samplers', 'core', 'options'])

    def actuate(self, state, send_over_p2p = True):
        """Updates all Knobs in the given state to the given values and optionally logs the state.

        Args:
            state (dict): Target state in nested dict form
        """
        for device in state:
            self.devices[device].actuate(state[device], send_over_p2p)

        self.buffer.add(state)

    def load(self):
        ''' Load knob states from file. '''
        try:
            with open(self.core.path['state']+self.name+'.json', 'r') as file:
                state = DataDict(json.load(file))
        except FileNotFoundError:
            state = DataDict({})
        self.state.patch(state.find('state', label=False))
        self.range.patch(state.find('min'))
        self.range.patch(state.find('max'))

    def save(self):
        ''' Save knob states to file. '''
        state = {}
        for device in self.state:
            state[device] = {}
            for knob in self.state[device]:
                state[device][knob] = {'state': self.state[device][knob],
                                      'min': self.range[device][knob]['min'],
                                      'max': self.range[device][knob]['max']}
        with open(self.core.path['state']+self.name+'.json', 'w') as file:
            json.dump(state, file, indent=2)

    def _on_load(self):
        """Tasks to be carried out after all Devices and Knobs are initialized."""
        for device in self.devices.values():
            device._connected = device._connect()
        self.actuate(self.state)
