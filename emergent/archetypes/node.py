import json
import os
import weakref
import pathlib
import time
import inspect
from emergent.archetypes.historian import Historian
from emergent.archetypes.optimizer import Optimizer
from emergent.archetypes.sampler import Sampler
from emergent.archetypes.state import State
from PyQt5.QtWidgets import QWidget
from emergent.utility import methodsWithDecorator
import logging as log
import pandas as pd
import datetime
from emergent.signals import ActuateSignal, SettingsSignal, RemoveSignal, CreateSignal
import numpy as np

class Node():
    ''' The Node class is the core building block of the EMERGENT network,
    providing useful organizational methods which are passed on to the Input,
    Device, and Control classes. '''

    instances = []
    ''' Contains all currently instantiated Nodes. This can
        be accessed for a given type, e.g. Control.instances lists all Control
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

    def get_root(self):
        ''' Returns the root Control node of any branch. '''
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

    # def __getattribute__(self, name):
    #     returned = object.__getattribute__(self, name)
    #     if inspect.isfunction(returned) or inspect.ismethod(returned):
    #         log.debug('called %s', returned.__name__)
    #     return returned

class Input(Node):
    ''' Input nodes represent physical variables which may affect the outcome of
        an experiment, such as laser frequency or beam alignment. '''

    instances = []
    ''' Contains all currently instantiated Nodes. This can
        be accessed for a given type, e.g. Control.instances lists all Control
        nodes. '''

    def __init__(self, name, parent):
        """Initializes an Input node, which is never directly used but instead
            offers a useful internal representation of a state.

        Args:
            name (str): node name. Nodes which share a Device should have unique names.
            parent (str): name of parent Device node.
        """
        super().__init__(name, parent=parent)
        self.state = None
        self.min = None
        self.max = None
        self.node_type = 'input'
        self.actuate_signal = ActuateSignal()
        self.settings_signal = SettingsSignal()
        self.parent.parent.dataframe[self.parent.name][self.name] = pd.DataFrame()

    def set_settings(self, d):
        if 'max' in d:
            self.max = d['max']
        if 'min' in d:
            self.min = d['min']
        self.parent.parent.settings[self.parent.name][self.name] = d
        self.settings_signal.emit({'min':self.min, 'max':self.max})

class Device(Node):
    ''' Device nodes represent apparatus which can control the state of Input
        nodes, such as a synthesizer or motorized actuator. '''

    instances = []
    ''' Contains all currently instantiated Nodes. This can
        be accessed for a given type, e.g. Control.instances lists all Control
        nodes. '''

    def __init__(self, name, parent):
        """Initializes a Device node.

        Args:
            name (str): node name. Devices which share a Control should have unique names.
            parent (str): name of parent Control node.
        """
        super().__init__(name, parent=parent)
        self.state = {}
        self.parent.state[self.name] = {}
        self.parent.settings[self.name] = {}
        self.parent.dataframe[self.name] = {}

        self.loaded = 0     # set to 1 after first state preparation
        self.node_type = 'device'

        ''' Add signals for input creation and removal '''
        self.create_signal = CreateSignal()
        self.remove_signal = RemoveSignal()

    def add_input(self, name):
        ''' Attaches an Input node with the specified name. This should correspond
            to a specific name in the _actuate() function of a non-abstract Device
            class: for example, the PicoAmp MEMS driver has inputs explicitly named
            'X' and 'Y' which are referenced in PicoAmp._actuate().'''
        input = Input(name, parent=self)
        self.children[name] = input
        if self.name not in self.parent.inputs:
            self.parent.inputs[self.name] = {}
        self.parent.inputs[self.name][name] = input
        self.parent.load(self.name, name)
        self.state[name] = self.children[name].state

        self.create_signal.emit(self.parent, self, name)
        if self.loaded:
            # self.actuate({name:self.parent.state[self.name][name]})
            log.warn('Inputs changed but not actuated; physical state not synched with virtual state. Run parent.actuate(parent.state) to resolve, where parent is the name of the parent control node.')

    def remove_input(self, name):
        ''' Detaches the Input node with the specified name. '''
        self.remove_signal.emit(self.parent, self, name)

        del self.children[name]
        del self.state[name]

        del self.parent.inputs[self.name][name]
        del self.parent.state[self.name][name]


    def _actuate(self, state):
        """Private placeholder for the device-specific driver.

        Note:
            State actuation is done by first calling the Device.actuate() method,
            which calls Device._actuate(state) to change something in the lab, then
            calls Device.update(state) to register this new state with EMERGENT.
            When you write a driver inheriting from Device, you should reimplement
            this method to update your device to the specified state only - do not
            update any stored states such as Device.state, Input.state, or Control.state
            from this method.

        Args:
            state (dict): Target state of the form {'param1':value1, 'param2':value2,...}.
        """
        return

    def _connect(self):
        """Private placeholder for the device-specific initiation method. """
        return 1

    def actuate(self, state):
        """Makes a physical device change in the lab with the _actuate() method, then registers this change with EMERGENT.

        Args:
            state (dict): Target state of the form {'param1':value1, 'param2':value2,...}.
        """

        self._actuate(state)
        self.update(state)

    def update(self,state):
        """Synchronously updates the state of the Input, Device, and Control.

        Args:
            state (dict): New state, e.g. {'param1':value1, 'param2':value2}.
        """
        t = datetime.datetime.now()
        for input in state:
            self.state[input] = state[input]    # update Device
            self.children[input].state = state[input]   # update Input
            self.parent.state[self.name][input] = state[input]   # update Control
            self.children[input].actuate_signal.emit(state[input])   # emit Qt signal

class Control(Node):
    ''' The Control node oversees connected Devices, allowing the Inputs to be
        algorithmically tuned to optimize some target function. '''

    instances = []
    ''' Contains all currently instantiated Nodes. This can
        be accessed for a given type, e.g. Control.instances lists all Control
        nodes. '''

    def __init__(self, name, parent = None, path = '.'):
        """Initializes a Control node and attaches Historian and Optimizer instances.

        Args:
            name (str): node name. All Control nodes should have unique names.
            parent (str): name of parent Control node. Note: child Control nodes are currently not supported and may lead to unpredictable behavior.
            path (str): network path relative to the emergent/ folder. For example, if the network.py file is located in emergent/networks/example, then path should be 'networks/example.'

        """

        super().__init__(name, parent)
        self.inputs = {}
        self.state = State()
        self.settings = {}
        self.actuating = 0
        self.cycle_time = 0
        self.state_path = path+'/state/'
        self.data_path = path+'/data/'
        self.dataframe = {}
        self.dataframe['cost'] = {}
        for p in [self.state_path, self.data_path]:
            pathlib.Path(p).mkdir(parents=True, exist_ok=True)

        self.historian = Historian(self)
        self.optimizers = {}
        self.samplers = {}

        self.node_type = 'control'
        self.load_costs()

    def actuate(self, state, save=True):
        """Updates all Inputs in the given state to the given values and optionally logs the state.

        Args:
            state (dict): Target state of the form {'deviceA.param1':1, 'deviceA.param1':2,...}
            save (bool): Whether or not to log.
        """
        # if not self.actuating:
            # self.actuating = 1
        ''' Aggregate states by device '''
        dev_states = {}
        for dev in state:
            self.children[dev].actuate(state[dev])
        #     self.actuating = 0
        # else:
        #     log.warn('Actuate blocked by already running actuation.')

    def attach_optimizer(self, state, cost):
        optimizer = Optimizer(self, cost=cost)
        index = len(self.optimizers)
        self.optimizers[index] = {'state':state, 'optimizer':optimizer, 'status':'Ready'}
        return optimizer, index

    def attach_sampler(self, state, cost, optimizer = None):
        if optimizer is None:
            sampler = Sampler(self, cost=cost)
        else:
            sampler = optimizer.sampler
            sampler.optimizer = optimizer
        index = len(self.samplers)
        self.samplers[index] = {'state':state, 'sampler':sampler, 'status':'Ready'}
        return sampler, index

    def list_costs(self):
        """Returns a list of all methods tagged with the '@experiment' decorator."""
        return methodsWithDecorator(self.__class__, 'experiment')

    def list_errors(self):
        """Returns a list of all methods tagged with the '@error' decorator."""
        return methodsWithDecorator(self.__class__, 'error')


    def load(self, device, name):
        """Loads the last saved state and attempts to reinitialize previous values for the Input node specified by full_name. If the input did not exist in the last state, then it is initialized with default values.

        Args:
            full_name (str): Specifies the Input node and its parent device, e.g. 'deviceA.input1'.
        """

        full_name = self.name + '.' + device + '.' + name

        ''' Load dataframe '''
        try:
            self.dataframe[device][name] = pd.read_csv(self.data_path+full_name+'.csv', index_col=0)
            self.state[device][name] = self.dataframe[device][name]['state'].iloc[-1]
            self.settings[device][name] = {}
            for setting in ['min', 'max']:
                self.settings[device][name][setting] = self.dataframe[device][name][setting].iloc[-1]
            self.inputs[device][name].set_settings(self.settings[device][name])


        except FileNotFoundError:
            self.dataframe[device][name] = pd.DataFrame()
            self.state[device][name] = 0
            self.settings[device][name] = {}
            for setting in ['min', 'max']:
                self.settings[device][name][setting] = 0
            log.warn('Could not find csv for input %s; creating new settings.'%full_name)

    def load_costs(self):
        for cost_name in self.list_costs():
            try:
                self.dataframe['cost'][cost_name] = pd.read_csv(self.data_path+self.name+'.'+cost_name+'.csv', index_col=0)
            except (FileNotFoundError, pd.errors.EmptyDataError):
                self.dataframe['cost'][cost_name] = pd.DataFrame()

    def save(self, tag = ''):
        """Aggregates the self.state and self.settings variables into a dataframe and saves to csv.

        Args:
            tag (str): Label written to the third column of the log file which describes where the state was saved from, e.g. 'actuate' or 'optimize'.
        """
        ''' Save dataframes to csv '''
        t= datetime.datetime.now()
        for dev in self.inputs:
            for input in self.inputs[dev]:
                self.save_dataframe(t, dev, input)

        for name in self.dataframe['cost']:
            self.dataframe['cost'][name].to_csv(self.data_path+self.name+'.'+name+'.csv')

    def save_dataframe(self, t, dev, input_name):
        full_name = self.name + '.' + dev + '.' + input_name
        input = self.inputs[dev][input_name]
        self.update_dataframe(t, dev, input_name, input.state)
        self.dataframe[dev][input_name].to_csv(self.data_path+full_name+'.csv')

    def update_dataframe(self, t, dev, input_name, state):
        self.dataframe[dev][input_name].loc[t, 'state'] = state
        for setting in ['min', 'max']:
            self.dataframe[dev][input_name].loc[t, setting] = self.settings[dev][input_name][setting]

    def update_cost(self, t, cost, name):
        self.dataframe['cost'][name].loc[t, name] = cost
        for dev in self.children.values():
            for input in dev.children.values():
                self.dataframe['cost'][name].loc[t, dev.name + ': ' + input.name] = input.state

    def onLoad(self):
        """Tasks to be carried out after all Devices and Inputs are initialized."""
        for device in self.children.values():
            device._connected = device._connect()
            device.loaded = 1
        self.actuate(self.state)
