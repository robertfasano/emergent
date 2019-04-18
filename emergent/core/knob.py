'''
    A Knob represents a physical quantity that you can set in the lab, like a
    voltage or a mirror position. The Knob class simply tracks a value for a
    "knob" in your experiment.
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
