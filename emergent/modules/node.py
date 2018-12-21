import json
import os
import weakref
import time
import inspect
from emergent.modules import Sampler, State, recommender, ProcessHandler
from PyQt5.QtWidgets import QWidget
import logging as log
import pandas as pd
import datetime
from emergent.signals import RemoveSignal, CreateSignal, ActuateSignal, ProcessSignal
import numpy as np
from emergent.utility import StateBuffer, MacroBuffer, get_address

class Node():
    ''' The Node class is the core building block of the EMERGENT network,
    providing useful organizational methods which are passed on to the Input,
    Thing, and Hub classes. '''

    instances = []
    ''' Contains all currently instantiated Nodes. This can
        be accessed for a given type, e.g. Hub.instances lists all Hub
        nodes. '''

    def __init__(self, name, parent=None):
        ''' Initializes a Node with a name and optionally registers
            to a parent. '''
        self.name = name
        self.__class__.instances.append(weakref.proxy(self))
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

    instances = []
    ''' Contains all currently instantiated Nodes. This can
        be accessed for a given type, e.g. Hub.instances lists all Hub
        nodes. '''

    def __init__(self, name, parent):
        """Initializes an Input node, which is never directly used but instead
            offers a useful internal representation of a state.

        Args:
            name (str): node name. Nodes which share a Thing should have unique names.
            parent (str): name of parent Thing.
        """
        super().__init__(name, parent=parent)
        self.state = None
        self.node_type = 'input'

class Thing(Node):
    ''' Things represent apparatus which can control the state of Input
        nodes, such as a synthesizer or motorized actuator. '''

    instances = []
    ''' Contains all currently instantiated Nodes. This can
        be accessed for a given type, e.g. Hub.instances lists all Hub
        nodes. '''

    def __init__(self, name, parent, params = {}):
        """Initializes a Thing.

        Args:
            name (str): node name. Things which share a Hub should have unique names.
            parent (str): name of parent Hub.
        """
        self.local = True
        if not parent.local:
            self.local = False
            return
        super().__init__(name, parent=parent)
        self.state = {}
        self.params = params
        self.parent.state[self.name] = {}
        self.parent.settings[self.name] = {}

        self.loaded = 0     # set to 1 after first state preparation
        self.node_type = 'thing'

        ''' Add signals for input creation and removal '''
        self.signal = ActuateSignal()
        self.create_signal = CreateSignal()
        self.remove_signal = RemoveSignal()

    def __getstate__(self):
        d = {}
        ignore = ['signal', 'create_signal', 'remove_signal']
        unpickled = []
        for item in ignore:
            if hasattr(self, item):
                unpickled.append(getattr(self,item))
        for item in self.__dict__:
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

        self.create_signal.emit(self.parent, self, name)
        if self.loaded:
            # self.actuate({name:self.parent.state[self.name][name]})
            log.warn('Inputs changed but not actuated; physical state not synched with virtual state. Run parent.actuate(parent.state) to resolve, where parent is the name of the parent hub node.')

    def remove_input(self, name):
        ''' Detaches the Input node with the specified name. '''
        self.remove_signal.emit(self.parent, self, name)
        del self.children[name]
        del self.state[name]
        del self.parent.state[self.name][name]


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
            state (dict): Target state of the form {'param1':value1, 'param2':value2,...}.
        """
        return

    def _connect(self):
        """Private placeholder for the thing-specific initiation method. """
        return 1

    def actuate(self, state):
        """Makes a physical thing change in the lab with the _actuate() method, then registers this change with EMERGENT.

        Args:
            state (dict): Target state of the form {'param1':value1, 'param2':value2,...}.
        """

        self._actuate(state)
        self.update(state)
        self.signal.emit(state)

    def update(self,state):
        """Synchronously updates the state of the Input, Thing, and Hub.

        Args:
            state (dict): New state, e.g. {'param1':value1, 'param2':value2}.
        """
        t = datetime.datetime.now()
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

    instances = []
    ''' Contains all currently instantiated Nodes. This can
        be accessed for a given type, e.g. Hub.instances lists all Hub
        nodes. '''

    def __init__(self, name, addr = None, network = None, parent = None):
        """Initializes a Hub.

        Args:
            name (str): node name. All Hubs should have unique names.
            parent (str): name of parent Hub. Note: child Hubs are currently not supported and may lead to unpredictable behavior.
            path (str): network path relative to the emergent/ folder. For example, if the network.py file is located in emergent/networks/example, then path should be 'networks/example.'

        """
        self.watchdogs = {}
        self.network = network
        self.name = name
        self.addr = addr
        self.manager = ProcessHandler()
        if self.addr is None:
            self.addr = get_address()
        if network.addr != addr and addr is not None:
            self.local = False
            return
        else:
            self.local = True
        super().__init__(name, parent)
        self.state = State()
        self.settings = {}
        self.samplers = {}
        self.node_type = 'hub'
        self.signal = ActuateSignal()
        self.process_signal = ProcessSignal()

    def __getstate__(self):
        d = {}
        ignore = ['watchdogs', 'signal', 'process_signal', 'samplers', 'network']
        unpickled = []
        for item in ignore:
            if hasattr(self, item):
                unpickled.append(getattr(self,item))
        for item in self.__dict__:
            if self.__dict__[item] not in unpickled:
                d[item] = self.__dict__[item]
        return d

    def actuate(self, state):
        """Updates all Inputs in the given state to the given values and optionally logs the state.

        Args:
            state (dict): Target state of the form {'thingA.param1':1, 'thingA.param1':2,...}
        """
        ''' Aggregate states by thing '''
        thing_states = {}
        for thing in state:
            self.children[thing].actuate(state[thing])
        self.signal.emit(state)

        self.buffer.add(state)

    # def load(self, thing, name):
    #     """Loads the last saved state and attempts to reinitialize previous values for the Input node specified by full_name. If the input did not exist in the last state, then it is initialized with default values.
    #     """
    #     if thing not in self.state:
    #         self.state[thing] = {}
    #     try:
    #         with open(self.network.state_path+self.name+'.json', 'r') as file:
    #             state = json.load(file)
    #
    #         self.state[thing][name] = state[thing][name]['state']
    #         self.settings[thing][name] = {}
    #         for setting in ['min', 'max']:
    #             self.settings[thing][name][setting] = state[thing][name][setting]
    #     except Exception as e:
    #         print('Exception:', e)
    #         self.state[thing][name] = 0
    #         self.settings[thing][name] = {}
    #         for setting in ['min', 'max']:
    #             self.settings[thing][name][setting] = 0
    #         log.warn('Could not find csv for input %s; creating new settings.'%name)

    def check_lock(self):
        ''' Check if any of the monitored signals are outside a threshold. Return True if not. '''
        locked = False
        ''' Block until all watchdogs are enabled and locked '''
        while not locked:
            locked = True
            for w in self.watchdogs.values():
                locked = locked and not w.reacting              # if a watchdog is reacting, we are unlocked
                if w.enabled:
                    locked = locked and w.check()           # check the watchdog state
            if not locked:
                time.sleep(0.1)
        return

    def enable_watchdogs(self, enabled):
        for w in self.watchdogs.values():
            w.enabled = enabled

    def load(self):
        try:
            with open(self.network.state_path+self.name+'.json', 'r') as file:
                state = json.load(file)
        except FileNotFoundError:
            state = {}
        for thing in self.children.values():
            for input in thing.children.values():
                try:
                    self.state[thing.name][input.name] = state[thing.name][input.name]['state']
                    self.settings[thing.name][input.name] = {}
                    for setting in ['min', 'max']:
                        self.settings[thing.name][input.name][setting] = state[thing.name][input.name][setting]
                except Exception as e:
                    print('Exception:', e)
                    self.state[thing.name][input.name] = 0
                    self.settings[thing.name][input.name] = {'min': 0, 'max': 1}
                    log.warn('Could not find csv for input %s; creating new settings.'%input.name)

    def optimize(self, state, experiment_name, threaded = True, priority = False):
        if threaded:
            self.manager._run_thread(self.optimize_thread, args = (state, experiment_name, priority), stoppable = False)
        else:
            self.optimize_thread(state, experiment_name, priority)

    def optimize_thread(self, state, experiment_name, priority = False):
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
        sampler.priority = priority
        self.enable_watchdogs(False)
        sampler.algorithm.run(sampler.state)

        self.enable_watchdogs(True)
        sampler.active = False

    def save(self):
        state = {}
        for thing in self.state:
            state[thing] = {}
            for input in self.state[thing]:
                state[thing][input] = {}
                state[thing][input]['state'] = self.state[thing][input]
                state[thing][input]['min'] = self.settings[thing][input]['min']
                state[thing][input]['max'] = self.settings[thing][input]['max']

        with open(self.network.state_path+self.name+'.json', 'w') as file:
            json.dump(state, file)

    def onLoad(self):
        """Tasks to be carried out after all Things and Inputs are initialized."""
        for thing in self.children.values():
            thing._connected = thing._connect()
            thing.loaded = 1
        self.actuate(self.state)
