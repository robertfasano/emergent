import numpy as np
from archetypes.node import Control
from utility import cost

class TestControl(Control):
        def __init__(self, name, parent=None, path = '.'):
                super().__init__(name, parent, path=path)

        @cost
        def cost_coupled(self, state):
            return self.cost_uncoupled(state, theta=30*np.pi/180)

        @cost
        def cost_uncoupled(self, state, theta=0):
            self.actuate(state)
            x=self.state['deviceA.X']*np.cos(theta) - self.state['deviceA.Y']*np.sin(theta)
            y=self.state['deviceA.X']*np.sin(theta) + self.state['deviceA.Y']*np.cos(theta)
            x0 = 0.3
            y0 = 0.6
            return -np.exp(-(x-0.5)**2/x0**2)*np.exp(-(y-0.5)**2/y0**2)

        def scramble(self):
            for key in self.state.keys():
                self.state[key] = np.random.uniform()
