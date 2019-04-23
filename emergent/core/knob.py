'''
    A Knob represents a physical quantity that you can set in the lab, like a
    voltage or a mirror position. The Knob class simply tracks a value for a
    "knob" in your experiment.
'''
from emergent.core import Node
from emergent.utilities.persistence import __getstate__

class Knob(Node):
    ''' Knob nodes represent physical variables which may affect the outcome of
        an experiment, such as laser frequency or beam alignment. '''

    def __init__(self, name, device):
        """Initializes a Knob node, which is never directly used but instead
            offers a useful internal representation of a state.

        Args:
            name (str): node name. Nodes which share a Device should have unique names.
            device (str): name of parent Device.
        """
        super().__init__(name)
        # self.state = None
        self.node_type = 'knob'

        self.__getstate__ = lambda: __getstate__(['device', 'options'])
