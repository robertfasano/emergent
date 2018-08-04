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
    def __init__(self, name, parent=None):
        ''' Initializes a Node with a name and optionally registers
            to a parent. '''
        self.name = name
        self.type = None
        self.__class__.instances.append(weakref.proxy(self))
        self.children = {}
        if parent is not None:
            self.register(parent)
        self.root = self.get_root()

    # def add_child(self, children):
    #     assert type(children) is list
    #     for child in children:
    #             self.children.append(child)

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
        instances = []
        def __init__(self, name, parent):
                super().__init__(name, parent=parent)
                #self.__class__.instances.append(weakref.proxy(self))
                self.value = None
                self.full_name = self.parent.name+'.'+self.name

        def set(self, value):
                ''' Calls the parent Device.actuate() function to change self.value to a new value '''
                self.parent.actuate({self.name:value})

class Device(Node):
        instances = []
        def __init__(self, name, parent):
                super().__init__(name, parent=parent)
                #self.__class__.instances.append(weakref.proxy(self))
                self.state = {}
                self.inputs = {}

        def add_input(self, name):
            ''' Attaches an Input node with the specified parameters '''
            self.children[name] = Input(name, parent=self)
            self.parent.get_inputs()
            self.parent.get_settings()
            self.get_state()
            self.parent.get_state()

        def _actuate(self, state):
                ''' Private placeholder, gets overwritten when adding a Device '''
                return

        def actuate(self, state):
                ''' Calls self.device._actuate() and updates self.state'''
                self._actuate(state)
                self.update(state)

        def update(self,state):
                ''' Updates self.state to new variables stored in state dict '''
                for key in state.keys():
                                self.state[key] = state[key]

                ''' format state dict and update parent '''
                for key in state.keys():
                    parent_key = self.name+'.'+key
                    self.parent.state[parent_key] = state[key]

        def get_state(self):
            self.state = {}
            for i in self.inputs.keys():
                self.state[i] = self.inputs[i].value

        def get_settings(self):
            self.settings = {}
            for i in self.inputs.keys():
                self.settings[i] = {'min': self.inputs[i].min, 'max': self.inputs[i].max}

        # def register(self, parent):
        #         ''' Adds self to parent control '''
        #         self.parent = parent
        #         self.parent.add_device(self.name, self)


class Control(Node):
        instances = []
        def __init__(self, name, parent = None, path = '.'):
                super().__init__(name, parent)
                #self.__class__.instances.append(weakref.proxy(self))
                self.devices = {}
                self.inputs = {}
                self.state = {}
                self.actuating = 0
                self.settings_path =path+'/settings/'
                self.state_path = path+'/state/'

                self.clock = Clock(self)
                self.historian = Historian(self)
                self.optimizer = Optimizer(self)
                for p in [self.settings_path, self.state_path]:
                        # os.makedirs(p, exist_ok=True)
                        pathlib.Path(p).mkdir(parents=True, exist_ok=True)

        def add_device(self, name, device):
            self.devices[name] = device

        def list_costs(self):
            return methodsWithDecorator(self.__class__, 'cost')

        def get_inputs(self):
            ''' Adds all connected Inputs of child Device nodes to self.inputs. An input is accessible through a key of the format 'Device.Input', e.g. 'MEMS.X' '''
            for dev in list(self.children.values()):
                for i in list(dev.children.values()):
                    name = dev.name+'.'+i.name
                    self.inputs[name] = i

        def get_state(self):
                ''' Reads the state of all Inputs, and adds to a total state dict. '''
                self.state = {}
                for i in self.inputs.keys():
                    self.state[i] = self.inputs[i].value

        def get_settings(self):
            self.settings = {}
            try:
                with open(self.settings_path+self.name+'.txt', 'r') as file:
                    saved_settings=json.loads(file.readlines()[-1].split('\t')[1])
                with open(self.state_path+self.name+'.txt', 'r') as file:
                    saved_state=json.loads(file.readlines()[-1].split('\t')[1])
                loaded = 1
            except FileNotFoundError:
                loaded = 0

            for i in self.inputs.keys():
                try:
                    self.settings[i] = {'min': self.inputs[i].min, 'max': self.inputs[i].max}
                except AttributeError:
                    resp = ''
                    saved = 0
                    if loaded:
                        if i in saved_settings.keys() and i in saved_state.keys():
                            saved = 1
                            #print('Load from file? (y/n)')
                            #resp = input()
                            print('%s settings loaded from file.'%i)
                            resp = 'y'
                            if resp == 'y':
                                for x in ['min', 'max']:
                                    setattr(self.inputs[i],x,saved_settings[i][x])
                                self.settings[i] = saved_settings[i]
                                self.state[i] = saved_state[i]
                                self.inputs[i].value = self.state[i]
                    if resp == 'n' or not saved:
                        print('Please enter initial value: ')
                        self.inputs[i].value = float(input())
                        print('Please enter min: ')
                        self.inputs[i].min = float(input())
                        print('Please enter max: ')
                        self.inputs[i].max = float(input())

                        self.save()
                        self.get_settings()

        def actuate(self, state, save=True):
            ''' Updates all Inputs in the given state to the given values. Argument should have keys of the form 'Device.Input', e.g. state={'MEMS.X':0} '''
            if not self.actuating:
                self.actuating = 1
                for i in state.keys():
                                self.inputs[i].set(state[i])
                self.actuating = 0

                self.save()
                if self.window is not None:
                    self.window.update_state(self.name)
            else:
                print('Actuate blocked by already running actuation.')

        def save(self):
                ''' Saves the current state to a text file '''
                paths = [self.settings_path, self.state_path]
                data = [self.settings, self.state]

                for i in range(len(paths)):
                    filename = paths[i]+self.name+'.txt'

                    write_newline = False
                    if os.path.isfile(filename):
                        write_newline = True

                    with open(filename, 'a') as file:
                        if write_newline:
                            file.write('\n')
                        file.write('%f\t%s'%(time.time(),json.dumps(data[i])))

        def load(self):
                ''' Loads a state from a text file'''
                paths = [self.settings_path, self.state_path]
                state = {}
                vars = [self.settings, state]

                for i in range(len(paths)):
                    filename = paths[i]+self.name+'.txt'
                    with open(filename, 'r') as file:
                	    vars[i]=json.loads(file.readlines()[-1].split('\t')[1])
                self.actuate(state)
