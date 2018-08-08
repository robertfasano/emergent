import json
import os
import weakref
import pathlib
import time
from archetypes.clock import Clock
from archetypes.historian import Historian
from archetypes.optimizer import Optimizer
from utility import methodsWithDecorator

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

class Input(Node):
    ''' Input nodes represent physical variables which may affect the outcome of
        an experiment, such as laser frequency or beam alignment. '''

    instances = []
    ''' Contains all currently instantiated Nodes. This can
        be accessed for a given type, e.g. Control.instances lists all Control
        nodes. '''

    def __init__(self, name, parent, type='real', speed = 'slow'):
        """Initializes an Input node.

        Args:
            name (str): node name. Nodes which share a Device should have unique names.
            parent (str): name of parent Device node.
            type (str): Specifies whether the Input node is 'real' (representing a directly controlled quantity) or 'virtual' (representing a derived quantity or superposition of real quantities).
            speed (str): Specified whether the Input node is 'slow' (using state-actuation for sequencing) or 'fast' (using burst streaming from a LabJack).
        """
        super().__init__(name, parent=parent)
        self.type = type
        self.state = None
        self.sequence = None
        self.full_name = self.parent.name+'.'+self.name
        self.min = None
        self.max = None
        self.node_type = 'input'

    def set(self, state):
        """Requests actuation from the parent Device.

        Note:
            Virtual nodes can only be updated after the first state preparation.
            During network initialization, the Control node loads the previous
            states of the real nodes and actuates them; after this is finished,
            the virtual states are computed and updated.

        Args:
            state (float): Target value.
        """
        if self.type is 'real' or self.parent.loaded:
            self.parent.actuate({self.name:state})

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
        self.real_inputs = 0
        self.virtual_inputs = 0
        self.node_type = 'device'

    def add_input(self, name, type='real'):
        ''' Attaches an Input node with the specified name. This should correspond
            to a specific name in the _actuate() function of a non-abstract Device
            class: for example, the PicoAmp MEMS driver has inputs explicitly named
            'X' and 'Y' which are referenced in PicoAmp._actuate().'''

        input = Input(name, parent=self, type=type)
        self.children[name] = input
        self.parent.inputs[input.full_name] = input
        self.parent.load(input.full_name)
        self.state[name] = self.children[name].state

        if type == 'real':
            self.real_inputs += 1
        elif type == 'virtual':
            self.virtual_inputs += 1

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
            If a virtual state is passed in (i.e. all dict keys label virtual Input nodes),
            then the state will be converted to real using Device.virtual_to_real(),
            which must be implemented in any driver file which uses virtual inputs.
            After actuation of the real state, the equivalent virtual state is
            updated.

        Note:
            If a mixed state is passed in (with both real and virtual components),
            only the real components will be used.


        Args:
            state (dict): Target state of the form {'param1':value1, 'param2':value2,...}.
        """


        ''' First prepare a pure real state. If the passed state is mixed between
            real and virtual components, only the real components will be used. '''
        real = self.is_type(state, 'real')
        virtual = self.is_type(state, 'virtual')
        if real and virtual:
            state = self.get_type(state, 'real')
            virtual = False
            print('WARNING: only real components are being used of a mixed real/virtual state.')
        if virtual:
            state = self.virtual_to_real(state)

        ''' Now actuate and update '''
        self._actuate(state)
        self.update(state)
        if self.loaded and self.virtual_inputs > 0:
            self.update(self.real_to_virtual(state))

    def get_missing_keys(self, state, keys):
        """Returns the state dict with any missing keys filled in from self.state.

        Note:
            This is useful when using virtual functions which depend on multiple
            inputs. Consider two inputs X and Y with two virtual inputs u=X+Y
            and v=X-Y. If we actuate just X or Y, the virtual inputs still need
            to know the value of the non-actuated input to update their state.
            This method pulls the latest value of any parameters specified in
            keys so that the virtual inputs can be calculated.

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
        """Returns the real/virtual components of the state according to the passed type.

        Args:
            state (dict): Target state, e.g. {'param1':value1, 'param2':value2}.
            type (str): Input node type ('real' or 'virtual').

        Returns:
            new_state (dict): State dict containing the real or virtual elements of state.
        """
        new_state = {}
        for key in state.keys():
            if self.children[key].type == type:
                new_state[key] = state[key]
        return new_state

    def is_type(self, state, type):
        """Checks whether the state is real or virtual according to the passed in type.
        Note:
            is_type(state,'real')==False does not mean the state is virtual - it could be mixed!

        Args:
            state (dict): State dict, e.g. {'param1':value1, 'param2':value2}.
            type (str): Input node type ('real' or 'virtual').

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
        for key in state.keys():
            self.state[key] = state[key]    # update Device
            self.children[key].state = state[key]   # update Input
            parent_key = self.name+'.'+key
            self.parent.state[parent_key] = state[key]   # update Control

class Control(Node):
    ''' The Control node oversees connected Devices, allowing the Inputs to be
        algorithmically tuned to optimize some target function. '''

    instances = []
    ''' Contains all currently instantiated Nodes. This can
        be accessed for a given type, e.g. Control.instances lists all Control
        nodes. '''

    def __init__(self, name, parent = None, path = '.'):
        """Initializes a Control node and attaches Clock, Historian, and Optimizer instances.

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
        self.settings_path =path+'/settings/'
        self.state_path = path+'/state/'
        self.sequence_path = path+'/sequence/'
        self.data_path = path+'/data/'
        for p in [self.settings_path, self.state_path, self.sequence_path, self.data_path]:
            pathlib.Path(p).mkdir(parents=True, exist_ok=True)

        self.clock = Clock(self)
        self.historian = Historian(self)
        self.optimizer = Optimizer(self)

        self.node_type = 'control'

    def get_sequence(self):
        """Populates the self.sequence dict with sequences of all inputs."""
        for i in self.inputs.values():
            self.sequence[i.full_name] = i.sequence

    def list_costs(self):
        """Returns a list of all methods tagged with the '@cost' decorator."""
        return methodsWithDecorator(self.__class__, 'cost')

    def actuate(self, state, save=True):
        """Updates all Inputs in the given state to the given values and optionally logs the state.

        Args:
            state (dict): Target state of the form {'deviceA.param1':1, 'deviceA.param1':2,...}
            save (bool): Whether or not to log.
        """
        if not self.actuating:
            self.actuating = 1

            for i in state.keys():
                self.inputs[i].set(state[i])
            self.actuating = 0
            if save:
                self.save(tag='actuate')
            if hasattr(self, 'window'):
                self.window.update_state(self.name)
        else:
            print('Actuate blocked by already running actuation.')

    def save(self, tag = ''):
        """Aggregates the self.state, self.settings, self.cycle_time, and self.sequence variables into a single dict and saves to file.

        Args:
            tag (str): Label written to the third column of the log file which describes where the state was saved from, e.g. 'actuate' or 'optimize'.
        """
        state = {}
        state['cycle_time'] = self.cycle_time
        for input in self.inputs.values():
            full_name = input.full_name
            state[full_name] = {}
            state[full_name]['state'] = self.state[full_name]
            state[full_name]['settings'] = self.settings[full_name]
            state[full_name]['sequence'] = self.sequence[full_name]

        filename = self.state_path + self.name + '.txt'
        write_newline = os.path.isfile(filename)

        with open(filename, 'a') as file:
            if write_newline:
                file.write('\n')
            file.write('%f\t%s\t%s'%(time.time(),json.dumps(state), tag))

    def load(self, full_name):
        """Loads the last saved state and attempts to reinitialize previous values for the Input node specified by full_name. If the input did not exist in the last state, then it is initialized with default values.

        Args:
            full_name (str): Specifies the Input node and its parent device, e.g. 'deviceA.input1'.
        """
        filename = self.settings_path + self.name + '.txt'
        try:
            with open(filename, 'r') as file:
                state = json.loads(file.readlines()[-1].split('\t')[1])
        except FileNotFoundError:
            state = {}

        ''' Load variables into control '''
        try:
            self.settings[full_name] = state[full_name]['settings']
            self.state[full_name] = state[full_name]['state']
            self.sequence[full_name] = state[full_name]['sequence']
            self.cycle_time = state[full_name]['cycle_time']
        except KeyError:
            self.settings[full_name] = {'min':0, 'max':1}
            self.state[full_name] = 0
            self.sequence[full_name] = [[0,0]]
            self.cycle_time = 0

        ''' Update sequence of inputs '''
        self.inputs[full_name].sequence = self.sequence[full_name]

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

    def onLoad(self):
        """Tasks to be carried out after all Devices and Inputs are initialized."""
        self.actuate(self.state)
        for device in self.children.values():
            device.loaded = 1
            if device.virtual_inputs > 0:
                device.update(device.real_to_virtual(device.state))

        self.clock.prepare_sequence()
