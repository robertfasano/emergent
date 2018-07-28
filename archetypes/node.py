import architecture.graph as graph
from emergent.devices.manager import open_device

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
        self.parent.add_child(self)

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
        def __init__(self, name, device, network, parent, id=None):
                super().__init__(name, parent=parent)
                if id is None:
                        self.id = network.generate_id()
                self.device = open_device(device)
                
                self.state = {}
                self.inputs = {}
                
        def add_input(self, name, value, min, max):
                ''' Attaches an Input node with the specified parameters '''
                self.inputs[name] = Input(name, value, min, max, parent=self)
                
        def _actuate(state):
                ''' Private placeholder, gets overwritten when adding a Device '''
                return
        
        def actuate(state):
                ''' Calls self.device._actuate() and updates self.state'''
                self._actuate(state)
                self.update(state)
                
        def update(state):
                ''' Updates self.state to new variables stored in state dict '''
                for key in state.keys():
                                self.state[key] = state[key]
                        
class Control(Node):
        def __init__(self, name, parent, cost):
                super().__init__(name, parent)
                self.cost = cost
                self.devices = {}
                self.inputs = {}
                self.state = {}
                
        def add_device(self, name, device, network, id=None):
                self.devices[name] = Device(name, device, network, self, id)
                
        def get_inputs(self):
                ''' Adds all connected Inputs of child Device nodes to self.inputs. An input is accessible through a key of the format 'Device.Input', e.g. 'MEMS.X' '''
                for dev in self.devices.values():
                                for i in dev.inputs.values():
                                                name = dev.name+'.'+input.name
                                                self.inputs[name] = i
        def get_state(self):
                ''' Reads the state of all Inputs, and adds to a total state dict. '''
                for i in self.inputs.keys():
                                self.state[i] = self.inputs[i].value
                                
        def actuate(self, state):
                ''' Updates all Inputs in the given state to the given values. Argument should have keys of the form 'Device.Input', e.g. state={'MEMS.X':0} '''
                for i in self.state.keys():
                                self.inputs[i].set(self.state[i])
                                
if __name__ == '__main___':
        from labAPI.devices.Node import Node
        ''' Example network construction '''
        # create a PicoAmp Device Node and add X and Y input nodes 
        args = ()
        a = Node(name='MEMS', device = PicoAmp, args = args, layer = 0) 
        a.add_input(['X','Y'])
        
        # create a NetControls Device Node and add Z input node
        args = ()
        b = Node(name='feedthrough', device = NetControls, args = args, layer=0)
        b.add_input('Z')
        
        # create a Process node and add a and b
        c = Node(name='MOT', cost = cost, args = args)
        c.add_child([a,b])
        
        
        
        
        