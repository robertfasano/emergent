import json
import os

class Node():
    def __init__(self, name, parent=None):
        ''' Initializes a Node with a name and optionally registers
            to a parent. If layer is None, then the layer is automatically
            calculated from the network topology. Layer should be 0 for
            bottom-level Nodes.
            Device Nodes can be initialized by passing in a device/arg tuple,
            e.g. (Device, args)'''
        self.name = name
        self.type = None

        self.children = []
        if parent is not None:
                self.register(parent)

    def add_child(self, children):
        assert type(children) is list
        for child in children:
                self.children.append(child)

    def register(self, parent):
        ''' Register self with parent node '''
        self.parent = parent


class Input(Node):
        def __init__(self, name, value, min, max, parent):
                super().__init__(name, parent=parent)
                self.value = value
                self.min = min
                self.max = max

        def set(self, value):
                ''' Calls the parent Device.actuate() function to change self.value to a new value '''
                self.parent.actuate({self.name:value})


class Device(Node):
        def __init__(self, name, parent, id=None):
                super().__init__(name, parent=parent)
                self.id = id
                self.state = {}
                self.inputs = {}

        def add_input(self, name, value, min, max):
                ''' Attaches an Input node with the specified parameters '''
                self.inputs[name] = Input(name, value, min, max, parent=self)
                self.get_state()
                self.parent.get_inputs()
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
            for i in self.inputs.keys():
                self.state[i] = self.inputs[i].value

        def register(self, parent):
                ''' Adds self to parent control '''
                self.parent = parent
                self.parent.add_device(self.name, self)

class Control(Node):
        def __init__(self, name, parent = None):
                super().__init__(name, parent)
                self.devices = {}
                self.inputs = {}
                self.state = {}

                self.settings_path =  './settings/'

                if not os.path.exists(self.settings_path):
                                os.makedirs(self.settings_path)


        def add_device(self, name, device):
                self.devices[name] = device

        def cost(state):
                return

        def get_inputs(self):
                ''' Adds all connected Inputs of child Device nodes to self.inputs. An input is accessible through a key of the format 'Device.Input', e.g. 'MEMS.X' '''
                for dev in list(self.devices.values()):
                                for i in list(dev.inputs.values()):
                                                name = dev.name+'.'+i.name
                                                self.inputs[name] = i
        def get_state(self):
                ''' Reads the state of all Inputs, and adds to a total state dict. '''
                for i in self.inputs.keys():
                                self.state[i] = self.inputs[i].value

        def actuate(self, state):
                ''' Updates all Inputs in the given state to the given values. Argument should have keys of the form 'Device.Input', e.g. state={'MEMS.X':0} '''
                for i in state.keys():
                                self.inputs[i].set(state[i])


        def save(self):
                ''' Saves the current state to a text file '''
                filename = self.settings_path+self.name+'.txt'
                with open(filename, 'w') as file:
                                json.dump(self.state, file)

        def load(self):
                ''' Loads a state from a text file'''
                filename = self.settings_path+self.name+'.txt'
                with open(filename, 'r') as file:
                	state=json.load(file)
                self.actuate(state)
