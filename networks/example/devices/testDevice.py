from archetypes.node import Device
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

        ''' Define virtual inputs which are rotated 30 degrees relative to the
            real ones '''
        self.add_input('u', type='virtual')
        self.add_input('v', type='virtual')

    def _actuate(self, state, type='any'):
        ''' Usually this method would change a physical state, but for our
            virtual network we only print the argument (note: the virtual state
            is updated within the public calling method Device.actuate()).'''

        ''' If state contains mixed real/virtual inputs, only actuate the real '''
        print(state)
        real = self.is_real(state)
        virtual = self.is_virtual(state)
        if real and virtual:
            state = self.get_real(state)
            virtual = False
        if real and type is not 'real':
            self.update(self.real_to_virtual(state))
        elif type is not 'real':
            self.update(self.virtual_to_real(state))

    def get_real(state):
        new_state = {}
        for key in state.keys():
            if self.children[key].type == 'real':
                new_state[key] = state[key]
        return new_state

    def is_real(self, state):
        ''' Return True if all elements of the state are real.'''
        real = True
        for key in state.keys():
            real = real and (self.children[key].type == 'real')
        return real

    def is_virtual(self, state):
        ''' Return True if all elements of the state are real.'''
        virtual = True
        for key in state.keys():
            virtual = virtual and (self.children[key].type == 'virtual')
        return virtual

    def real_to_virtual(self, state):
        try:
            X = state['X']
        except KeyError:
            X = self.state['X']
        try:
            Y = state['Y']
        except KeyError:
            Y = self.state['Y']
        theta = 30*np.pi/180
        u = X*np.cos(theta)-Y*np.sin(theta)
        v = X*np.sin(theta)+Y*np.cos(theta)
        virtual = {'u':u, 'v':v}
        print(virtual)
        return virtual

    def virtual_to_real(self, state):
        try:
            u = state['u']
        except KeyError:
            u = self.state['u']
        try:
            v = state['v']
        except KeyError:
            v = self.state['v']

        theta = 30*np.pi/180
        X = u*np.cos(-theta)-v*np.sin(-theta)
        Y = u*np.sin(-theta)+v*np.cos(-theta)

        return {'X':X, 'Y':Y}
