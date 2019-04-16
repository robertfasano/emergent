''' 
    A Hub is an object which controls one or more Things to regulate the outcome
    of an experiment. For example, for beam alignment into an optical fiber we would
    require one or more Things for mirror control, as well as a Hub which measures
    the transmitted power and coordinates commands to its connected Things to maximize
    the signal. The Hub class also contains methods for saving and loading states
    to/from file, for monitoring important variables through the Watchdog framework,
    and for optimizing itself by interfacing with other modules.
'''
import json
import time
import logging as log
import datetime
# from emergent.modeling import Sampler
from emergent.utilities.containers import DataDict
from emergent.utilities import recommender
from emergent.utilities.networking import get_address, get_local_addresses
from emergent.core import Node, ProcessHandler

class Hub(Node):
    ''' The Hub oversees connected Things, allowing the Knobs to be
        algorithmically tuned to optimize some target function. '''

    def __init__(self, name, params={}, addr='127.0.0.1', core=None, parent=None):
        """Initializes a Hub.

        Args:
            name (str): node name. All Hubs should have unique names.
            parent (str): name of parent Hub. Note: child Hubs are currently not supported and may lead to unpredictable behavior.
            path (str): network path relative to the emergent/ folder. For example, if the network.py file is located in emergent/networks/example, then path should be 'networks/example.'

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
        self.watchdogs = {}
        self.core = core
        self.name = name
        self.addr = addr
        self.manager = ProcessHandler()
        if self.addr is None:
            self.addr = get_address()
        # if core.addr != addr and addr is not None:
        if self.addr not in get_local_addresses():
            self.local = False
            return
        self.local = True
        super().__init__(name, parent)
        # self.state = State()
        self.state = DataDict()
        self.range = DataDict()
        self.samplers = {}
        self.node_type = 'hub'
        self.ignored = []
        ''' Establish switch interface '''
        self.switches = {}

        # self.renaming = {'MEMS': {'name': 'mems', 'knobs':{'X': {'name': 'x'}}}}

    def __getstate__(self):
        d = {}
        ignore = ['root', 'watchdogs', 'samplers', 'core', 'leaf', 'options']
        ignore.extend(self.ignored)
        unpickled = []
        for item in ignore:
            if hasattr(self, item):
                unpickled.append(item)
        for item in self.__dict__:
            obj = getattr(self, item)
            if hasattr(obj, 'picklable'):
                if not obj.picklable:
                    continue
            if item not in unpickled:
                d[item] = self.__dict__[item]
        return d

    def actuate(self, state, send_over_p2p = True):
        """Updates all Knobs in the given state to the given values and optionally logs the state.

        Args:
            state (dict): Target state of the form {'thingA.param1':1, 'thingA.param1':2,...}
        """
        ''' Aggregate states by thing '''
        thing_states = {}
        for thing in state:
            self.children[thing].actuate(state[thing], send_over_p2p)


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
        for thing in self.state:
            state[thing] = {}
            for knob in self.state[thing]:
                node = self.children[thing].children[knob]
                state[thing][node.name] = {}
                state[thing][node.name]['state'] = self.state[thing][knob]
                state[thing][node.name]['min'] = self.range[thing][knob]['min']
                state[thing][node.name]['max'] = self.range[thing][knob]['max']
                state[thing][node.name]['display name'] = self.children[thing].children[knob].display_name
        with open(self.core.path['state']+self.name+'.json', 'w') as file:
            json.dump(state, file)

    def _on_load(self):
        """Tasks to be carried out after all Things and Knobs are initialized."""
        for thing in self.children.values():
            thing._connected = thing._connect()
            thing.loaded = 1
        self.actuate(self.state)
