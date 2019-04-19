''' Implements the Node class, which contains methods for relating EMERGENT building
    blocks to one another. Three further classes inherit from Node: the Knob, Thing,
    and Hub.
'''
from emergent.utilities.buffers import StateBuffer, MacroBuffer

class Node():
    ''' The Node class is the core building block of the EMERGENT network,
    providing useful organizational methods which are passed on to the Knob,
    Thing, and Hub classes. '''

    def __init__(self, name, parent=None):
        ''' Initializes a Node with a name and optionally registers
            to a parent. '''
        self.name = name
        self.children = {}
        if parent is not None:
            self.register(parent)
        self.options = {}
        self.buffer = StateBuffer(self)
        self.macro_buffer = MacroBuffer(self)

    def register(self, parent):
        ''' Register self with parent node. '''
        self.parent = parent
        parent.children[self.name] = self
