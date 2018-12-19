from emergent.modules import Thing
import numpy as np

class TestThing(Thing):
    ''' Thing driver for the virtual network in the 'basic' example. '''
    def __init__(self, name, parent, inputs):
        ''' Register with the network and create two Input nodes, 'X' and 'Y'. '''
        super().__init__(name, parent)
        if not self._instantiated:
            return
        for input in inputs:
            self.add_input(input)

    def _actuate(self, state):
        ''' Usually this method would change a physical state, but for our
            virtual network we only print the argument (note: the virtual state
            is updated within the public calling method Thing.actuate()).'''
        # print(state)
        return

    def _connect(self):
        return 1
