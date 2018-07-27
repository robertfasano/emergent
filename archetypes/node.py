import architecture.graph as graph

class Node():
    def __init__(self, name, device = None, cost = None, parent=None, layer = None):
        ''' Initializes a Node with a name and optionally registers 
            to a parent. If layer is None, then the layer is automatically
            calculated from the network topology. Layer should be 0 for 
            bottom-level Nodes. 
            Device Nodes can be initialized by passing in a device/arg tuple,
            e.g. (Device, args)'''
        self.name = name
        
        ''' Add device/cost if this is a Device/Process node '''
        self.type = 'input'
        if device is not None:
                self.device = device[0](args=device[1])
                self.type = 'device'
        if cost is not None:
                self.daq = cost[2][0](args=cost[2][1])
                self.cost = cost[0](args=cost[1])
                self.type = 'control'
        assert not (cost is not None) and (device is not None)
                
        self.children = []
        if parent is not None:
                self.register(parent)
        
        self.state = {}
        
    def add_child(self, children):
        assert type(children) is list
        for child in children:
                self.children.append(child)
                self.concatenate()
        
    def add_input(self, input):
        return
        
    def register(self, parent):
        ''' Register self with parent node '''
        self.parent = parent
        self.parent.add_child(self)
        
    def concatenate(self):
        ''' Prepare nested dict of child states '''
        if len(self.children) > 0:
            for child in self.children:
                state[child.name] = child.state
                
    def unravel(self):
        ''' Decomposes composite state recursively downward '''
        return 
        
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
        
    def setup(self):
        return
        
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
        
        
        
        
        