import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-3]))
from emergent.archetypes.node import Control, Device
from emergent.archetypes.Optimizer import Optimizer

import numpy as np

class TestDevice(Device):
        def __init__(self, name, parent):
                super().__init__(name, parent)
                
        def _actuate(self, state):
                print(state)

class TestControl(Control):
        def __init__(self, name, parent=None):
                super().__init__(name, parent)
                self.optimizer = Optimizer(self)
                self.clock = Clock(self)

        def cost(self, state):
                self.actuate(state)
                x0 = .3
                cost = -1
                for x in self.state.values():
                        cost *= np.exp(-x**2/x0**2)
                return cost

        def cost_coupled(self, state):
            return cost_coupled(state, theta=30*np.pi/180)
            
        def cost_uncoupled(self, state, theta=0):
            x=self.state['deviceA.X']*np.cos(theta) - self.state['deviceA.Y']*np.sin(theta)
            y=self.state['deviceA.X']*np.sin(theta) + self.state['deviceA.Y']*np.cos(theta)
            x0 = 0.3
            y0 = 0.6
            return np.exp(-(x-0.5)**2/x0**2)*np.exp(-(y-0.5)**2/y0**2)
            
        def scramble(self):
            for key in self.state.keys():
                self.state[key] = np.random.uniform()


control = TestControl('control')

deviceA = TestDevice('deviceA', parent=control)
deviceA.add_input('X')
deviceA.add_input('Y')

deviceB = TestDevice('deviceB', parent=control)
deviceB.add_input('Z')

control.get_state()
control.get_settings()
#control.scramble()
#params = {'method':'L-BFGS-B', 'tol':1e-7, 'plot':False}
#control.optimizer.optimize(state=control.state, cost=control.cost, method='skl_minimize', params=params)

deviceA.inputs['X'] = [(0,0), (0.5, 1)]
deviceA.inputs['Y'] = [(0,0), (0.25,-1), (0.5,0), (0.75, 1)]
control.clock.add_input(deviceA.inputs['X'])
control.clock.add_input(deviceA.inputs['Y'])
control.clock.start(1)

