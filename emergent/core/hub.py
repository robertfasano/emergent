''' Implements the Node class, which contains methods for relating EMERGENT building
    blocks to one another. Three further classes inherit from Node: the Knob, Thing,
    and Hub.

    A Knob represents a physical quantity that you can set in the lab, like a
    voltage or a mirror position. The Knob class simply tracks a value for a
    "knob" in your experiment.

    A Thing is some sort of actuator that can control the state of Knobs, like a
    DAC (for voltage generation) or a voltage driver for MEMS or motorized mirror
    mounts. The user must write a device driver script which implements the actuate()
    method to define the interface between EMERGENT and the manufacturer API. The Thing
    class also contains methods for updating the macroscopic state representation
    after actuation and for adding or removing knobs dynamically.

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
# from emergent.modules import Sampler
from emergent.utilities.containers import DataDict
from emergent.utilities import recommender
from emergent.utilities.networking import get_address, get_local_addresses
from emergent.core import Node, ProcessHandler

class Hub(Node):
    ''' The Hub oversees connected Things, allowing the Knobs to be
        algorithmically tuned to optimize some target function. '''

    def __init__(self, name, params={}, addr='127.0.0.1', network=None, parent=None):
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
            network_params = network.params[name]
        except KeyError:
            network.params[name] = {}
            network_params = {}
        for p in network_params:
            self.params[p] = network_params[p]
        if 'name' in network_params:
            name = network_params['name']
        self.watchdogs = {}
        self.network = network
        self.name = name
        self.addr = addr
        self.manager = ProcessHandler()
        if self.addr is None:
            self.addr = get_address()
        # if network.addr != addr and addr is not None:
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
        ignore = ['root', 'watchdogs', 'samplers', 'network', 'leaf', 'options']
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

    def _check_lock(self, block=False):
        ''' Return True if none of the monitored signals are outside a threshold. '''
        if len(self.watchdogs) == 0:
            return
        locked = False
        ''' Block until all watchdogs are enabled and locked '''
        states = {}
        while not locked:
            locked = True
            for w in self.watchdogs.values():
                locked = locked and not w.reacting # if a watchdog is reacting, we are unlocked
                if w.enabled:
                    c = w.check()
                    locked = locked and c          # check the watchdog state
                    states[w.name] = w.value
            ''' Here, add overall watchdog state to a queue to write to the database '''
            # self.network.database.write(states, measurement = 'watchdog')
            if not block:
                return
            if not locked:
                time.sleep(0.1)

        return

    def enable_watchdogs(self, enabled):
        ''' Enable or disable all attached watchdogs. '''
        for w in self.watchdogs.values():
            w.enabled = enabled

    # def load(self):
    #     ''' Load knob states from file. '''
    #     try:
    #         with open(self.network.path['state']+self.name+'.json', 'r') as file:
    #             state = json.load(file)
    #     except FileNotFoundError:
    #         state = {}
    #
    #     for thing in self.children.values():
    #         thing_children = list(thing.children.values())
    #         for knob in thing_children:
    #             try:
    #                 if 'display name' in state[thing.name][knob.name]:
    #                     display_name = state[thing.name][knob.name]['display name']
    #                     self.children[thing.name].children[knob.name].display_name = display_name
    #                     self.children[thing.name].children[display_name] = self.children[thing.name].children.pop(knob.name)
    #                     self.children[thing.name].state[display_name] = self.children[thing.name].state.pop(knob.name)
    #                 self.state[thing.name][knob.display_name] = state[thing.name][knob.name]['state']
    #                 self.range[thing.name][knob.display_name] = {}
    #                 for setting in ['min', 'max']:
    #                     self.range[thing.name][knob.display_name][setting] = state[thing.name][knob.name][setting]
    #             except Exception as e:
    #                 self.state[thing.name][knob.display_name] = 0
    #                 self.range[thing.name][knob.display_name] = {'min': 0, 'max': 1}
    #                 log.warning('Could not find csv for knob %s; creating new settings.', knob.display_name)

    def load(self):
        ''' Load knob states from file. '''
        try:
            with open(self.network.path['state']+self.name+'.json', 'r') as file:
                state = DataDict(json.load(file))
        except FileNotFoundError:
            state = DataDict({})
        self.state.patch(state.find('state', label=False))
        self.range.patch(state.find('min'))
        self.range.patch(state.find('max'))




    def optimize(self, state, experiment_name, threaded=True, skip_lock_check=False):
        ''' Launch an optimization. '''
        if threaded:
            self.manager._run_thread(self._optimize_thread,
                                     args=(state, experiment_name, skip_lock_check),
                                     stoppable=False)
        else:
            self._optimize_thread(state, experiment_name, skip_lock_check)

    def _optimize_thread(self, state, experiment_name, skip_lock_check=False):
        ''' Optimizes an experiment with the default settings from file '''
        experiment_params = recommender.load_experiment_parameters(self, experiment_name)
        algorithm = recommender.get_default_algorithm(self, experiment_name)
        algorithm_params = recommender.load_algorithm_parameters(self, experiment_name, algorithm.name)
        start_time = datetime.datetime.now().strftime('%Y%m%dT%H%M')
        experiment = getattr(self, experiment_name)

        sampler = Sampler(algorithm.name,
                          state,
                          self,
                          experiment,
                          experiment_params,
                          algorithm,
                          algorithm_params,
                          t=start_time)
        sampler.skip_lock_check = skip_lock_check
        self.enable_watchdogs(False)
        sampler.algorithm.run(sampler.state)

        self.enable_watchdogs(True)
        sampler.active = False

    def __rename_knob(self, node, name):
        thing = node.parent
        self.state[thing.name][name] = self.state[thing.name].pop(node.display_name)
        self.range[thing.name][name] = self.range[thing.name].pop(node.display_name)

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
        with open(self.network.path['state']+self.name+'.json', 'w') as file:
            json.dump(state, file)

    def _on_load(self):
        """Tasks to be carried out after all Things and Knobs are initialized."""
        for thing in self.children.values():
            thing._connected = thing._connect()
            thing.loaded = 1
        self.actuate(self.state)
