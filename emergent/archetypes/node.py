import json
import os
import weakref
import pathlib
import time
import inspect
from emergent.archetypes.sequencer import Sequencer
from emergent.archetypes.historian import Historian
from emergent.archetypes.optimizer import Optimizer
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal, QObject
from emergent.utility import methodsWithDecorator
import logging as log
import pandas as pd
import datetime

class ActuateSignal(QObject):
    signal = pyqtSignal(float)

    def __init__(self):
        super().__init__()

    def connect(self, func):
        self.signal.connect(func)

    def emit(self, state):
        self.signal.emit(state)

class SettingsSignal(QObject):
    signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

    def connect(self, func):
        self.signal.connect(func)

    def emit(self, sequence):
        self.signal.emit(sequence)

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

    def __getattribute__(self, name):
        returned = object.__getattribute__(self, name)
        if inspect.isfunction(returned) or inspect.ismethod(returned):
            log.debug('called %s', returned.__name__)
        return returned

class Input(Node):
    ''' Input nodes represent physical variables which may affect the outcome of
        an experiment, such as laser frequency or beam alignment. '''

    instances = []
    ''' Contains all currently instantiated Nodes. This can
        be accessed for a given type, e.g. Control.instances lists all Control
        nodes. '''

    def __init__(self, name, parent, type='primary', speed = 'slow'):
        """Initializes an Input node, which is never directly used but instead
            offers a useful internal representation of a state.

        Args:
            name (str): node name. Nodes which share a Device should have unique names.
            parent (str): name of parent Device node.
            type (str): Specifies whether the Input node is 'primary' (representing a directly controlled quantity) or 'secondary' (representing a derived quantity or superposition of primary quantities).
            speed (str): Specified whether the Input node is 'slow' (using state-actuation for sequencing) or 'fast' (using burst streaming from a LabJack).
        """
        super().__init__(name, parent=parent)
        self.type = type
        self.state = None
        self.sequence = None
        self.full_name = self.parent.name+'.'+self.name
        self.min = None
        self.max = None
        self.sequenced = 0
        self.node_type = 'input'
        self.actuate_signal = ActuateSignal()
        self.settings_signal = SettingsSignal()

    def set_settings(self, d):
        if 'max' in d:
            self.max = d['max']
        if 'min' in d:
            self.min = d['min']
        self.parent.parent.settings[self.full_name] = d
        self.settings_signal.emit({'min':self.min, 'max':self.max})

    def set_sequence(self, sequence):
        ''' Sets the sequence of an Input and pushes changes upstream.

            Args:
                sequence (list): a list of lists, each containing a time and a value.
        '''
        self.sequence = sequence
        self.sequenced = 1      # enable sequenced output
        self.parent.parent.sequence[self.full_name] = sequence
        self.parent.parent.sequencer.prepare_sequence()
        self.sequence_signal.emit(self.parent.parent.master_sequence)

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
        self.loaded = 0     # set to 1 after first state preparation
        self.primary_inputs = 0
        self.secondary_inputs = 0
        self.node_type = 'device'
        self.input_type = 'primary'

    def use_inputs(self, type):
        ''' Switches between primary and secondary input representations.

            Args:
                type (str): 'primary' or 'secondary'
        '''
        assert type in ['primary', 'secondary']
        if type == self.input_type:
            return

        ''' Get new state representation '''
        if type == 'secondary':
            new_state = self.primary_to_secondary(self.state)
        elif type == 'primary':
            new_state = self.secondary_to_primary(self.state)

        ''' Convert master sequence '''
        new_sequence = []
        for i in range(len(self.parent.master_sequence)):
            point = self.parent.master_sequence[i]
            delay = point[0]
            state = point[1]
            dev_state = {}
            for full_name in state.keys():
                if full_name.split('.')[0] == self.name:
                    name = full_name.split('.')[1]
                    dev_state[name] = state[full_name]
            state = dev_state

            if type == 'secondary':
                new = self.primary_to_secondary(state)
            else:
                new = self.secondary_to_primary(state)
            new_sequence.append([delay, new])
            for name in self.state.keys():
                full_name = self.name + '.' + name
                if self.children[name].sequenced:
                    del self.parent.master_sequence[i][1][full_name]
            for name in new_state.keys():
                full_name = self.name + '.' + name
                if self.children[name].sequenced:
                    self.parent.master_sequence[i][1][full_name] = new[name]

        ''' Change representation in parent control node '''
        for key in self.state.keys():
            full_name = self.name + '.' + key
            del self.parent.state[full_name]
        for key in new_state.keys():
            full_name = self.name + '.' + key
            self.parent.state[full_name] = new_state[key]
            self.children[key].state = new_state[key]

        ''' Convert settings '''
        min = {}
        max = {}
        for key in self.state.keys():
            full_name = self.name + '.' + key
            min[key] = self.parent.settings[full_name]['min']
            max[key] = self.parent.settings[full_name]['max']
        if type is 'primary':
            min_new = self.secondary_to_primary(min)
            max_new = self.secondary_to_primary(max)
        else:
            min_new = self.primary_to_secondary(min)
            max_new = self.primary_to_secondary(max)
        for key in min_new:
            self.children[key].set_settings({'min':min_new[key],'max':max_new[key]})
        for key in self.state.keys():
            full_name = self.name + '.' + key
            del self.parent.settings[full_name]

        ''' Update self '''
        self.state = new_state
        self.input_type = type

        ''' Convert subsequence - must be done after changing self.state '''
        for name in new_state.keys():
            full_name = self.name + '.' + name
            seq = self.parent.sequencer.master_to_subsequence(full_name)
            self.parent.inputs[full_name].sequence = seq

    def add_input(self, name, type='primary'):
        ''' Attaches an Input node with the specified name. This should correspond
            to a specific name in the _actuate() function of a non-abstract Device
            class: for example, the PicoAmp MEMS driver has inputs explicitly named
            'X' and 'Y' which are referenced in PicoAmp._actuate().'''

        input = Input(name, parent=self, type=type)
        self.children[name] = input
        self.parent.inputs[input.full_name] = input
        self.parent.load(input.full_name)

        if type == 'primary':
            self.state[name] = self.children[name].state
            self.primary_inputs += 1
        elif type == 'secondary':
            self.secondary_inputs += 1

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

    def actuate(self, state):
        """Makes a physical device change in the lab with the _actuate() method, then registers this change with EMERGENT.

        Note:
            If a secondary state is passed in (i.e. all dict keys label secondary Input nodes),
            then the state will be converted to primary using Device.secondary_to_primary(),
            which must be implemented in any driver file which uses secondary inputs.
            After actuation of the primary state, the equivalent secondary state is
            updated.

        Note:
            If a mixed state is passed in (with both primary and secondary components),
            only the primary components will be used.

        Args:
            state (dict): Target state of the form {'param1':value1, 'param2':value2,...}.
        """

        isPrimary = self.is_type(state, 'primary')
        isSecondary = self.is_type(state, 'secondary')
        assert not (isPrimary and isSecondary)

        if isPrimary:
            self._actuate(state)
        elif isSecondary:
            self._actuate(self.secondary_to_primary(state))
        self.update(state)

    def get_missing_keys(self, state, keys):
        """Returns the state dict with any missing keys filled in from self.state.

        Note:
            This is useful when using secondary functions which depend on multiple
            inputs. Consider two inputs X and Y with two secondary inputs u=X+Y
            and v=X-Y. If we actuate just X or Y, the secondary inputs still need
            to know the value of the non-actuated input to update their state.
            This method pulls the latest value of any parameters specified in
            keys so that the secondary inputs can be calculated.

        Args:
            state (dict): Target state, e.g. {'param1':value1, 'param2':value2}.
            keys (list): List of parameters not contained in state, e.g. ['param3'].

        Returns:
            state (dict): State containing both specified changes and previous values, etc {'param1':value1,'param2':value2, 'param3':self.state['param3']}.
        """
        total_state = {}
        for key in keys:
            try:
                total_state[key] = state[key]
            except KeyError:
                total_state[key] = self.state[key]
        return total_state

    def get_type(self, state, type):
        """Returns the primary/secondary components of the state according to the passed type.

        Args:
            state (dict): Target state, e.g. {'param1':value1, 'param2':value2}.
            type (str): Input node type ('primary' or 'secondary').

        Returns:
            new_state (dict): State dict containing the primary or secondary elements of state.
        """
        new_state = {}
        for key in state.keys():
            if self.children[key].type == type:
                new_state[key] = state[key]
        return new_state

    def is_type(self, state, type):
        """Checks whether the state is primary or secondary according to the passed in type.
        Note:
            is_type(state,'primary')==False does not mean the state is secondary - it could be mixed!

        Args:
            state (dict): State dict, e.g. {'param1':value1, 'param2':value2}.
            type (str): Input node type ('primary' or 'secondary').

        Returns:
            is_type (bool): True if all elements of state are type; False otherwise.
        """
        is_type = True
        for key in state.keys():
            is_type = is_type and (self.children[key].type == type)
        return is_type

    def update(self,state):
        """Synchronously updates the state of the Input, Device, and Control.

        Args:
            state (dict): New state, e.g. {'param1':value1, 'param2':value2}.
        """
        t = datetime.datetime.now()
        for input_name in state:
            self.state[input_name] = state[input_name]    # update Device
            input = self.children[input_name]
            input.state = state[input_name]   # update Input
            self.parent.state[input.full_name] = state[input_name]   # update Control
            input.actuate_signal.emit(state[input_name])   # emit Qt signal

class Control(Node):
    ''' The Control node oversees connected Devices, allowing the Inputs to be
        algorithmically tuned to optimize some target function. '''

    instances = []
    ''' Contains all currently instantiated Nodes. This can
        be accessed for a given type, e.g. Control.instances lists all Control
        nodes. '''

    def __init__(self, name, parent = None, path = '.'):
        """Initializes a Control node and attaches Sequencer, Historian, and Optimizer instances.

        Args:
            name (str): node name. All Control nodes should have unique names.
            parent (str): name of parent Control node. Note: child Control nodes are currently not supported and may lead to unpredictable behavior.
            path (str): network path relative to the emergent/ folder. For example, if the network.py file is located in emergent/networks/example, then path should be 'networks/example.'

        """

        super().__init__(name, parent)
        self.inputs = {}
        self.state = {}
        self.settings = {}
        self.sequence = {}
        self.actuating = 0
        self.state_path = path+'/state/'
        self.data_path = path+'/data/'
        self.dataframe = {}
        self.dataframe['cost'] = None

        for p in [self.state_path, self.data_path]:
            pathlib.Path(p).mkdir(parents=True, exist_ok=True)

        self.sequencer = Sequencer(self)
        self.historian = Historian(self)
        self.optimizer = Optimizer(self)

        self.node_type = 'control'

    def actuate(self, state, save=True):
        """Updates all Inputs in the given state to the given values and optionally logs the state.

        Args:
            state (dict): Target state of the form {'deviceA.param1':1, 'deviceA.param1':2,...}
            save (bool): Whether or not to log.
        """
        if not self.actuating:
            self.actuating = 1
            ''' Aggregate states by device '''
            dev_states = {}
            for full_name in state:
                dev_name = full_name.split('.')[0]
                if dev_name not in dev_states:
                    dev_states[dev_name] = {}
                input_name = full_name.split('.')[1]
                dev_states[dev_name][input_name] = state[full_name]
            ''' Send states to devices '''
            for dev_name in dev_states:
                dev = self.children[dev_name]
                state = dev_states[dev_name]
                dev.actuate(state)

            self.actuating = 0
        else:
            log.warn('Actuate blocked by already running actuation.')

    def get_sequence(self):
        """Populates the self.sequence dict with sequences of all inputs."""
        for i in self.inputs.values():
            self.sequence[i.full_name] = i.sequence

    def get_subsequence(self, keys):
        """Returns a sequence dict containing only the specified keys.

        Args:
            keys (list): full_name variables of Input nodes to retrieve, e.g. ['deviceA.input1', 'deviceB.input1'].
        """
        sequence = {}
        for key in keys:
            sequence[key] = self.sequence[key]
        return sequence

    def get_substate(self, keys):
        """Returns a state dict containing only the specified keys.

        Args:
            keys (list): full_name variables of Input nodes to retrieve, e.g. ['deviceA.input1', 'deviceB.input1'].
        """
        state = {}
        for key in keys:
            state[key] = self.state[key]
        return state

    def list_costs(self):
        """Returns a list of all methods tagged with the '@cost' decorator."""
        return methodsWithDecorator(self.__class__, 'cost')

    def load(self, full_name):
        """Loads the last saved state and attempts to reinitialize previous values for the Input node specified by full_name. If the input did not exist in the last state, then it is initialized with default values.

        Args:
            full_name (str): Specifies the Input node and its parent device, e.g. 'deviceA.input1'.
        """
        if self.inputs[full_name].type is 'secondary':
            return

        filename = self.state_path + self.name + '.txt'
        try:
            with open(filename, 'r') as file:
                state = json.loads(file.readlines()[-1].split('\t')[1])
        except FileNotFoundError:
            state = {}
            log.warn('State file not found for Control node %s, creating one now.'%self.name)

        ''' Load variables into control '''
        try:
            self.sequence[full_name] = state[full_name]['sequence']
            self.cycle_time = state['cycle_time']
        except KeyError:
            self.sequence[full_name] = [[0,0]]
            self.cycle_time = 0
            log.warn('Could not retrieve settings for input %s; creating new settings.'%full_name)

        ''' Update sequence of inputs '''
        self.inputs[full_name].sequence = self.sequence[full_name]

        ''' Load dataframe '''
        try:
            self.dataframe[full_name] = pd.read_csv(self.data_path+full_name+'.csv', index_col=0)
            self.state[full_name] = self.dataframe[full_name]['state'].iloc[-1]
            self.settings[full_name] = {}
            for setting in ['min', 'max']:
                self.settings[full_name][setting] = self.dataframe[full_name][setting].iloc[-1]
            self.inputs[full_name].set_settings(self.settings[full_name])
        except FileNotFoundError:
            self.dataframe[full_name] = pd.DataFrame()
            self.state[full_name] = 0
            for setting in ['min', 'max']:
                self.settings[full_name] = 0
            log.warn('Could not find csv for input %s; creating new settings.'%full_name)

        if self.dataframe['cost'] is None:
            try:
                self.dataframe['cost'] = pd.read_csv(self.data_path+'cost'+'.csv', index_col=0)
            except FileNotFoundError:
                self.dataframe['cost'] = pd.Series()




    def save(self, tag = ''):
        """Aggregates the self.state, self.settings, self.cycle_time, and self.sequence variables into a single dict and saves to file.

        Args:
            tag (str): Label written to the third column of the log file which describes where the state was saved from, e.g. 'actuate' or 'optimize'.
        """
        state = {}
        state['cycle_time'] = self.cycle_time

        ''' Convert any secondary inputs to primary before saving '''
        converted = []
        for dev in self.children.values():
            if dev.input_type == 'secondary':
                dev.use_inputs('primary')
                converted.append(dev)
        for input in self.inputs.values():
            if input.type is 'secondary':
                continue
            full_name = input.full_name
            state[full_name] = {}
            state[full_name]['state'] = self.state[full_name]
            state[full_name]['settings'] = self.settings[full_name]
            state[full_name]['sequence'] = self.sequence[full_name]

        ''' Convert back '''
        for dev in converted:
            dev.use_inputs('secondary')
        filename = self.state_path + self.name + '.txt'
        write_newline = os.path.isfile(filename)

        with open(filename, 'a') as file:
            if write_newline:
                file.write('\n')
            file.write('%f\t%s\t%s'%(time.time(),json.dumps(state), tag))

        if tag == 'optimize':
            ''' Save dataframes to csv '''
            for full_name in self.inputs:
                input = self.inputs[full_name]
                if input.type is 'secondary':
                    continue
                self.dataframe[full_name].to_csv(self.data_path+full_name+'.csv')
            self.dataframe['cost'].to_csv(self.data_path+'cost'+'.csv')

    def update_dataframe(self, t, full_name, state):
        if self.inputs[full_name].type is 'secondary':
            return
        self.dataframe[full_name].loc[t, 'state'] = state
        for setting in ['min', 'max']:
            self.dataframe[full_name].loc[t, setting] = self.settings[full_name][setting]

    def update_cost(self, t, cost):
        self.dataframe['cost'].loc[t] = cost

    def onLoad(self):
        """Tasks to be carried out after all Devices and Inputs are initialized."""
        self.actuate(self.state)
        for device in self.children.values():
            device.loaded = 1

        self.sequencer.prepare_sequence()
