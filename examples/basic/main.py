import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-3]))
from emergent.archetypes.node import Control
from emergent.devices.test import TestDevice
from emergent.archetypes.Optimizer import Optimizer

import numpy as np

class TestControl(Control):
        def __init__(self, name, parent=None):
                super().__init__(name, parent)
                self.optimizer = Optimizer(self)
                
        def cost(state):
                self.actuate(state)
                x0 = .3
                cost = -1
                for x in self.state.values():
                        cost *= np.exp(-x**2/x0**2)
                return cost

control = TestControl('control')

deviceA = TestDevice('deviceA', parent=control)
deviceA.add_input('X', 0, 0, 1)
deviceA.add_input('Y', 0, 0, 1)

deviceB = TestDevice('deviceB', parent=control)
deviceB.add_input('Z', 0, 0, 1)

control.optimizer.optimize(state=control.state, cost=control.cost, method='grid_search)