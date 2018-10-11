from emergent.archetypes.node import Device
from utility import dev
import numpy as np
@dev
class TestDevice(Device):
    ''' Device driver for the virtual network in the 'basic' example. '''
    def __init__(self, name, parent):
        ''' Register with the network and create two Input nodes, 'X' and 'Y'. '''
        super().__init__(name, parent)
        self.add_input('X')
        self.add_input('Y')

        ''' Define secondary inputs which are rotated 30 degrees relative to the
            primary ones '''
        self.add_input('u', type='secondary')
        self.add_input('v', type='secondary')

    def _actuate(self, state):
        ''' Usually this method would change a physical state, but for our
            virtual network we only print the argument (note: the virtual state
            is updated within the public calling method Device.actuate()).'''
        print(state)
        ''' this is where you would do some actuation on the primary state '''

    def _connect(self):
        return 1

    def primary_to_secondary(self, state):
        ''' Converts a primary state to a secondary state. '''
        state = self.get_missing_keys(state, ['X','Y'])
        X = state['X']
        Y = state['Y']

        theta = 30*np.pi/180
        u = X*np.cos(theta)-Y*np.sin(theta)
        v = X*np.sin(theta)+Y*np.cos(theta)
        secondary = {'u':u, 'v':v}
        return secondary

    def secondary_to_primary(self, state):
        ''' Converts a secondary state to a primary state. '''
        state = self.get_missing_keys(state, ['u','v'])
        u = state['u']
        v = state['v']

        theta = 30*np.pi/180
        X = u*np.cos(-theta)-v*np.sin(-theta)
        Y = u*np.sin(-theta)+v*np.cos(-theta)

        return {'X':X, 'Y':Y}
