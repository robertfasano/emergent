from archetypes.node import Device
from utility import dev

@dev
class TestDevice(Device):
    ''' Device driver for the virtual network in the 'basic' example. '''
    def __init__(self, name, parent):
        ''' Register with the network and create two Input nodes, 'X' and 'Y'. '''
        super().__init__(name, parent)
        self.add_input('X')
        self.add_input('Y')

    def _actuate(self, state):
        ''' Usually this method would change a physical state, but for our
            virtual network we only print the argument (note: the virtual state
            is updated within the public calling method Device.actuate()).'''
        print(state)