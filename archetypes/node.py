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

    def __init__(self, name, parent):
        ''' Initializes an Input node. '''
        super().__init__(name, parent=parent)
        self.state = None
        self.sequence = None
        self.full_name = self.parent.name+'.'+self.name
        self.min = None
        self.max = None

    def set(self, state):
            ''' Calls the parent Device.actuate() function to change
                self.state to a new value '''
            self.parent.actuate({self.name:state})

class Device(Node):
    ''' Device nodes represent apparatus which can control the state of Input
        nodes, such as a synthesizer or motorized actuator. '''

    instances = []
    ''' Contains all currently instantiated Nodes. This can
        be accessed for a given type, e.g. Control.instances lists all Control
        nodes. '''

    def __init__(self, name, parent):
        ''' Initializes a Device node. '''
        super().__init__(name, parent=parent)
        self.state = {}

    def add_input(self, name):
        ''' Attaches an Input node with the specified name. This should correspond
            to a specific name in the _actuate() function of a non-abstract Device
            class: for example, the PicoAmp MEMS driver has inputs explicitly named
            'X' and 'Y' which are referenced in PicoAmp._actuate().'''

        input = Input(name, parent=self)
        self.children[name] = input
        self.parent.inputs[input.full_name] = input
        self.parent.load(input.full_name)
        self.state[name] = self.children[name].state


    def _actuate(self, state):
        ''' Private placeholder for the device-specific physical actuator which
            should be reimplemented in each driver file. The public method
            Device.actuate() calls this method to update the physical state,
            then the public method updates the virtual state. '''
        return

    def actuate(self, state):
        ''' Updates the physical and virtual state to a target state. The passed
            dict can contain one or all of the inputs: e.g. state={'X':1} updates
            only the 'X' input, while state={'X':1, 'Y':2} updates both 'X'
            and 'Y'. '''
        self._actuate(state)
        self.update(state)

    def update(self,state):
        ''' Synchronously updates the state of the Input, Device, and Control. '''
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
        ''' Initializes a Control node and attaches Clock, Historian, and Optimizer
            objects. '''
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


    def get_sequence(self):
        for i in self.inputs.values():
            self.sequence[i.full_name] = i.sequence

    def list_costs(self):
        ''' Returns a list of all methods tagged with the '@cost' decorator. '''
        return methodsWithDecorator(self.__class__, 'cost')

    # def get_settings(self):
    #     self.settings = {}
    #     try:
    #         with open(self.settings_path+self.name+'.txt', 'r') as file:
    #             saved_settings=json.loads(file.readlines()[-1].split('\t')[1])
    #         with open(self.state_path+self.name+'.txt', 'r') as file:
    #             saved_state=json.loads(file.readlines()[-1].split('\t')[1])
    #         loaded = 1
    #     except FileNotFoundError:
    #         loaded = 0
    #
    #     for i in self.inputs.keys():
    #         try:
    #             self.settings[i] = {'min': self.inputs[i].min, 'max': self.inputs[i].max}
    #         except AttributeError:
    #             resp = ''
    #             saved = 0
    #             if loaded:
    #                 if i in saved_settings.keys() and i in saved_state.keys():
    #                     saved = 1
    #                     #print('Load from file? (y/n)')
    #                     #resp = input()
    #                     print('%s settings loaded from file.'%i)
    #                     resp = 'y'
    #                     if resp == 'y':
    #                         for x in ['min', 'max']:
    #                             setattr(self.inputs[i],x,saved_settings[i][x])
    #                         self.settings[i] = saved_settings[i]
    #                         self.state[i] = saved_state[i]
    #                         self.inputs[i].value = self.state[i]
    #             if resp == 'n' or not saved:
    #                 print('Please enter initial value: ')
    #                 self.inputs[i].value = float(input())
    #                 print('Please enter min: ')
    #                 self.inputs[i].min = float(input())
    #                 print('Please enter max: ')
    #                 self.inputs[i].max = float(input())
    #
    #                 self.save()
    #                 self.get_settings()

    def actuate(self, state, save=True):
        ''' Updates all Inputs in the given state to the given values.
            Argument should have keys of the form 'Device.Input', e.g.
            state={'MEMS.X':0} '''
        if not self.actuating:
            self.actuating = 1

            for i in state.keys():
                self.inputs[i].set(state[i])
            self.actuating = 0
            self.save(tag='actuate')
            if hasattr(self, 'window'):
                self.window.update_state(self.name)
        else:
            print('Actuate blocked by already running actuation.')

    def save(self, tag = ''):
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

    def load(self, name):
        state = {}
        filename = self.settings_path + self.name + '.txt'
        with open(filename, 'r') as file:
            state = json.loads(file.readlines()[-1].split('\t')[1])
        print('loading',name)
        ''' Load variables into control '''
        try:
            self.settings[name] = state[name]['settings']
            self.state[name] = state[name]['state']
            self.sequence[name] = state[name]['sequence']
            self.cycle_time = state[name]['cycle_time']
        except KeyError:
            self.settings[name] = {'min':0, 'max':1}
            self.state[name] = 0
            self.sequence[name] = [[0,0]]
            self.cycle_time = 0

        ''' Update sequence of inputs '''
        self.inputs[name].sequence = self.sequence[name]

    def get_subsequence(self, keys):
        ''' Returns a sequence dict containing only the specified keys '''
        sequence = {}
        for key in keys:
            sequence[key] = self.sequence[key]
        return sequence

    def get_substate(self, keys):
        ''' Returns a state dict containing only the specified keys '''
        state = {}
        for key in keys:
            state[key] = self.state[key]
        return state

    def onLoad(self):
        self.actuate(self.state)
        self.clock.prepare_sequence()
