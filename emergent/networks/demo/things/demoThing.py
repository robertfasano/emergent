from emergent.modules import Thing
import numpy as np

class DemoThing(Thing):
    ''' Thing driver for the virtual network in the 'basic' example. '''
    def __init__(self, name, params = {'inputs': ['X']}, parent = None):
        ''' Register with the network and create two Input nodes, 'X' and 'Y'. '''
        super().__init__(name, parent, params = params)
        if not self.local:
            return

        for input in params['inputs']:
            self.add_input(input)

    def _actuate(self, state):
        ''' Usually this method would change a physical state, but for our
            virtual network we only print the argument (note: the virtual state
            is updated within the public calling method Thing.actuate()).'''
        # print(state)
        return

    def _connect(self):
        return 1
