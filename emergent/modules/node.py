''' Implements the Node class, which contains methods for relating EMERGENT building
    blocks to one another. Three further classes inherit from Node: the Input, Thing,
    and Hub.

    An Input represents a physical quantity that you can set in the lab, like a
    voltage or a mirror position. The Input class simply tracks a value for a
    "knob" in your experiment.

    A Thing is some sort of actuator that can control the state of Inputs, like a
    DAC (for voltage generation) or a voltage driver for MEMS or motorized mirror
    mounts. The user must write a device driver script which implements the actuate()
    method to define the interface between EMERGENT and the manufacturer API. The Thing
    class also contains methods for updating the macroscopic state representation
    after actuation and for adding or removing inputs dynamically.

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
from emergent.modules import Sampler, ProcessHandler
from emergent.utilities.containers import State
from emergent.utilities import recommender
from emergent.utilities.signals import DictSignal
from emergent.utilities.buffers import StateBuffer, MacroBuffer
from emergent.utilities.networking import get_address, get_local_addresses
from emergent.utilities.commandline import get_hub

class Node():
    ''' The Node class is the core building block of the EMERGENT network,
    providing useful organizational methods which are passed on to the Input,
    Thing, and Hub classes. '''

    def __init__(self, name, parent=None):
        ''' Initializes a Node with a name and optionally registers
            to a parent. '''
        self.name = name
        self.display_name = name
        self.children = {}
        if parent is not None:
            self.register(parent)
        self.root = self.get_root()
        self.options = {}
        self.buffer = StateBuffer(self)
        self.macro_buffer = MacroBuffer(self)

    def get_root(self):
        ''' Returns the root Hub of any branch. '''
        root = self
        while True:
            try:
                root = root.parent
            except AttributeError:
                return root

    def register(self, parent):
        ''' Register self with parent node. '''
        self.parent = parent
        parent.children[self.name] = self


class Input(Node):
    ''' Input nodes represent physical variables which may affect the outcome of
        an experiment, such as laser frequency or beam alignment. '''

    def __init__(self, name, parent):
        """Initializes an Input node, which is never directly used but instead
            offers a useful internal representation of a state.

        Args:
            name (str): node name. Nodes which share a Thing should have unique names.
            parent (str): name of parent Thing.
        """
        # self._name_ = name
        # hub = parent.parent
        # if parent._name_ in hub.renaming:
        #     if name in hub.renaming[parent._name_]['inputs']:
        #         name = hub.renaming[parent._name_]['inputs'][name]['name']
        super().__init__(name, parent=parent)
        self.state = None
        self.node_type = 'input'



    def rename(self, name):
        ''' Update Thing '''
        thing = self.parent
        hub = self.parent.parent
        thing.__rename_input(self, name)
        hub.__rename_input(self, name)
        self.display_name = name
        self.leaf.setText(0, name)

    def __getstate__(self):
        ''' When the pickle module attempts to serialize this node to file, it
            calls this method to obtain a dict to serialize. We intentionally omit
            any unpicklable objects from this dict to avoid errors. '''
        d = {}
        ignore = ['parent', 'root', 'leaf', 'options']
        unpickled = []
        for item in ignore:
            if hasattr(self, item):
                unpickled.append(getattr(self, item))

        for item in self.__dict__:
            obj = getattr(self, item)
            if hasattr(obj, 'picklable'):
                if not obj.picklable:
                    continue
            if self.__dict__[item] not in unpickled:
                d[item] = self.__dict__[item]
        return d

class Thing(Node):
    ''' Things represent apparatus which can control the state of Input
        nodes, such as a synthesizer or motorized actuator. '''

    def __init__(self, name, parent, params={}):
        """Initializes a Thing.

        Args:
            name (str): node name. Things which share a Hub should have unique names.
            parent (str): name of parent Hub.
        """
        self._name_ = name      # save hardcoded name as private variable
        self.local = True
        if not parent.local:
            self.local = False
            return
        self.params = params
        ''' Update self.params with any parameters associated with the Network '''
        try:
            network_params = parent.network.params[parent._name_]['params'][name]['params']
        except KeyError:
            network_params = {}
        for p in network_params:
            self.params[p] = network_params[p]
        if 'name' in self.params:
            name = self.params['name']


        # ''' Rename from hub dictionary '''
        # if name in parent.renaming:
        #     name = parent.renaming[name]['name']

        super().__init__(name, parent=parent)
        self._connected = 0
        self.state = {}
        # self.state = State()

        self.parent.state[self.name] = {}
        self.parent.range[self.name] = {}

        self.loaded = 0     # set to 1 after first state preparation
        self.node_type = 'thing'

        ''' Add signals for input creation and removal '''
        self.signal = DictSignal()
        self.create_signal = DictSignal()
        self.remove_signal = DictSignal()

        self.ignored = []       # objects to ignore during pickling

        ''' Add inputs passed in params dict '''
        if 'inputs' in self.params:
            for input in self.params['inputs']:
                self.add_input(input)

    def __getstate__(self):
        ''' When the pickle module attempts to serialize this node to file, it
            calls this method to obtain a dict to serialize. We intentionally omit
            any unpicklable objects from this dict to avoid errors. '''
        d = {}
        ignore = ['parent', 'root', 'leaf', 'options']
        ignore.extend(self.ignored)
        unpickled = []
        for item in ignore:
            if hasattr(self, item):
                unpickled.append(getattr(self, item))

        for item in self.__dict__:
            obj = getattr(self, item)
            if hasattr(obj, 'picklable'):
                if not obj.picklable:
                    continue
            if self.__dict__[item] not in unpickled:
                d[item] = self.__dict__[item]
        return d

    def add_input(self, name):
        ''' Attaches an Input node with the specified name. This should correspond
            to a specific name in the _actuate() function of a non-abstract Thing
            class: for example, the PicoAmp MEMS driver has inputs explicitly named
            'X' and 'Y' which are referenced in PicoAmp._actuate().'''
        input = Input(name, parent=self)
        self.children[name] = input
        self.state[name] = self.children[name].state
        self.parent.state[self.name][name] = None
        self.parent.range[self.name][name] = {}
        for qty in ['min', 'max']:
            self.parent.range[self.name][name][qty] = None
        self.create_signal.emit({'hub': self.parent, 'thing': self, 'input': name})
        #if self.loaded:
            # self.actuate({name:self.parent.state[self.name][name]})
            #log.warning('Inputs changed but not actuated; physical state not synced with virtual state. Run parent.actuate(parent.state) to resolve, where parent is the name of the parent hub node.')

    def remove_input(self, name):
        ''' Detaches the Input node with the specified name. '''
        self.remove_signal.emit({'hub': self.parent, 'thing': self, 'input': name})
        del self.children[name]
        del self.state[name]
        del self.parent.state[self.name][name]

    def __rename_input(self, node, name):
        self.state[name] = self.state.pop(node.display_name)
        self.children[name] = self.children.pop(node.display_name)
        self._rename_input(node, name)

    def _rename_input(self, node, name):
        ''' Reimplement if any class-specific tasks need to be done when renaming
            children '''

    def _actuate(self, state):
        """Private placeholder for the thing-specific driver.

        Note:
            State actuation is done by first calling the Thing.actuate() method,
            which calls Thing._actuate(state) to change something in the lab, then
            calls Thing.update(state) to register this new state with EMERGENT.
            When you write a driver inheriting from Thing, you should reimplement
            this method to update your thing to the specified state only - do not
            update any stored states such as Thing.state, Input.state, or Hub.state
            from this method.

        Args:
            state (dict): Target state such as {'param1':value1, 'param2':value2}.
        """
        return

    def _connect(self):
        """Private placeholder for the thing-specific initiation method. """
        return 1

    def _translate(self, state):
        ''' Convert a state with display names into a state with original names. '''
        new_state = {}
        for display_name in state:
            for node in self.children.values():
                if node.display_name == display_name:
                    new_state[node.name] = state[display_name]

        return new_state

    def actuate(self, state, send_over_p2p = True):
        """Makes a physical thing change in the lab with the _actuate() method, then registers this change with EMERGENT.

        Args:
            state (dict): Target state of the form {'param1':value1, 'param2':value2,...}.
        """
        ''' Translate to original input names to send to driver '''
        # print(state)
        # for input_name in state:
        #     input = self.children[input_name]
        #     if input_name != input._name_:
        #         state[input._name_] = state.pop(input.name)
        # print(state)
        translated_state = self._translate(state)
        self._actuate(translated_state)
        self.update(state)
        self.signal.emit(state)
        if send_over_p2p:
            self.parent.network.p2p.set('state', {self.parent.name: {self.name: state}})

    def update(self, state):
        """Synchronously updates the state of the Input, Thing, and Hub.

        Args:
            state (dict): New state, e.g. {'param1':value1, 'param2':value2}.
        """
        for input in state:
            self.state[input] = state[input]    # update Thing
            self.children[input].state = state[input]   # update Input
            self.parent.state[self.name][input] = state[input]   # update Hub

            ''' update state buffer '''
            self.children[input].buffer.add(state)
        self.buffer.add(self.state)


class Hub(Node):
    ''' The Hub oversees connected Things, allowing the Inputs to be
        algorithmically tuned to optimize some target function. '''

    def __init__(self, name, params={}, addr=None, network=None, parent=None):
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
        self.state = State()
        self.settings = {}
        self.samplers = {}
        self.node_type = 'hub'
        self.signal = DictSignal()
        self.process_signal = DictSignal()
        self.ignored = []
        ''' Establish switch interface '''
        self.switches = {}

        # self.renaming = {'MEMS': {'name': 'mems', 'inputs':{'X': {'name': 'x'}}}}

    def __getstate__(self):
        d = {}
        ignore = ['root', 'watchdogs', 'samplers', 'network', 'leaf', 'options']
        ignore.extend(self.ignored)
        unpickled = []
        for item in ignore:
            if hasattr(self, item):
                unpickled.append(getattr(self, item))
        for item in self.__dict__:
            obj = getattr(self, item)
            if hasattr(obj, 'picklable'):
                if not obj.picklable:
                    continue
            if self.__dict__[item] not in unpickled:
                d[item] = self.__dict__[item]
        return d

    def actuate(self, state, send_over_p2p = True):
        """Updates all Inputs in the given state to the given values and optionally logs the state.

        Args:
            state (dict): Target state of the form {'thingA.param1':1, 'thingA.param1':2,...}
        """
        ''' Aggregate states by thing '''
        thing_states = {}
        for thing in state:
            self.children[thing].actuate(state[thing], send_over_p2p)
        self.signal.emit(state)

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
        ''' Enable all attached watchdogs. '''
        for w in self.watchdogs.values():
            w.enabled = enabled

    def load(self):
        ''' Load input states from file. '''
        try:
            with open(self.network.path['state']+self.name+'.json', 'r') as file:
                state = json.load(file)
        except FileNotFoundError:
            state = {}

        for thing in self.children.values():
            thing_children = list(thing.children.values())
            for input in thing_children:
                try:
                    if 'display name' in state[thing.name][input.name]:
                        display_name = state[thing.name][input.name]['display name']
                        self.children[thing.name].children[input.name].display_name = display_name
                        self.children[thing.name].children[display_name] = self.children[thing.name].children.pop(input.name)
                        self.children[thing.name].state[display_name] = self.children[thing.name].state.pop(input.name)
                    self.state[thing.name][input.display_name] = state[thing.name][input.name]['state']
                    self.settings[thing.name][input.display_name] = {}
                    for setting in ['min', 'max']:
                        self.settings[thing.name][input.display_name][setting] = state[thing.name][input.name][setting]
                except Exception as e:
                    self.state[thing.name][input.display_name] = 0
                    self.settings[thing.name][input.display_name] = {'min': 0, 'max': 1}
                    log.warning('Could not find csv for input %s; creating new settings.', input.display_name)

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

    def __rename_input(self, node, name):
        thing = node.parent
        self.state[thing.name][name] = self.state[thing.name].pop(node.display_name)
        self.range[thing.name][name] = self.range[thing.name].pop(node.display_name)

    def save(self):
        ''' Save input states to file. '''
        state = {}
        for thing in self.state:
            state[thing] = {}
            for input in self.state[thing]:
                node = self.children[thing].children[input]
                state[thing][node.name] = {}
                state[thing][node.name]['state'] = self.state[thing][input]
                state[thing][node.name]['min'] = self.range[thing][input]['min']
                state[thing][node.name]['max'] = self.range[thing][input]['max']
                state[thing][node.name]['display name'] = self.children[thing].children[input].display_name
        with open(self.network.path['state']+self.name+'.json', 'w') as file:
            json.dump(state, file)

    def _on_load(self):
        """Tasks to be carried out after all Things and Inputs are initialized."""
        for thing in self.children.values():
            thing._connected = thing._connect()
            thing.loaded = 1
        self.actuate(self.state)
