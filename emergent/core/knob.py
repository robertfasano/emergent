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
from emergent.core import Node

class Knob(Node):
    ''' Knob nodes represent physical variables which may affect the outcome of
        an experiment, such as laser frequency or beam alignment. '''

    def __init__(self, name, parent):
        """Initializes a Knob node, which is never directly used but instead
            offers a useful internal representation of a state.

        Args:
            name (str): node name. Nodes which share a Thing should have unique names.
            parent (str): name of parent Thing.
        """
        # self._name_ = name
        # hub = parent.parent
        # if parent._name_ in hub.renaming:
        #     if name in hub.renaming[parent._name_]['knobs']:
        #         name = hub.renaming[parent._name_]['knobs'][name]['name']
        super().__init__(name, parent=parent)
        self.state = None
        self.node_type = 'knob'

    def __getstate__(self):
        ''' When the pickle module attempts to serialize this node to file, it
            calls this method to obtain a dict to serialize. We intentionally omit
            any unpicklable objects from this dict to avoid errors. '''
        d = {}
        ignore = ['parent', 'root', 'leaf', 'options']
        unpickled = []
        for item in ignore:
            if hasattr(self, item):
                unpickled.append(item)

        for item in self.__dict__:
            obj = getattr(self, item)
            if hasattr(obj, 'picklable'):
                if not obj.picklable:
                    continue
            if item not in unpickled:
                d[item] = self.__dict__[item]
        return d
