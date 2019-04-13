''' Implements the Node class, which contains methods for relating EMERGENT building
    blocks to one another. Three further classes inherit from Node: the Knob, Thing,
    and Hub.

    A Knob represents a physical quantity that you can set in the lab, like a
    voltage or a mirror position. The Knob class simply tracks a value for a
    "knob" in your experiment.

    A Thing is some sort of actuator that can control the state of Knobs, like a
    DAC (for voltage generation) or a voltage driver for MEMS or motorized mirror
    mounts. The user must write a device driver script which implements the actuate()
    method to define the interface between EMERGENT and the manufacturer API. The Thing
    class also contains methods for updating the macroscopic state representation
    after actuation and for adding or removing knobs dynamically.

    A Hub is an object which controls one or more Things to regulate the outcome
    of an experiment. For example, for beam alignment into an optical fiber we would
    require one or more Things for mirror control, as well as a Hub which measures
    the transmitted power and coordinates commands to its connected Things to maximize
    the signal. The Hub class also contains methods for saving and loading states
    to/from file, for monitoring important variables through the Watchdog framework,
    and for optimizing itself by interfacing with other modules.
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
        self.display_name = name
        self.children = {}
        if parent is not None:
            self.register(parent)
        self.root = self.get_root()
        self.options = {}
        self.buffer = StateBuffer(self)
        self.macro_buffer = MacroBuffer(self)

    def exec_option(self, option):
        self.options[option]()

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
