''' A dummy device solely for testing the EMERGENT architecture. '''
import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-2]))
sys.path.append('C:\\Users\\Robbie\\Documents\\GitHub')
from emergent.archetypes.node import Device, Control
import numpy as np

def gaussian(state):
        x0 = .3
        cost = -1
        for x in state.values():
                cost *= np.exp(-x**2/x0**2)
        return cost
        
class TestDevice(Device):
        def __init__(self, name, parent):
                super().__init__(name, parent)
                self.add_input('X')
                self.add_input('Y')
                
        def _actuate(state):
                return
         
class TestControl(Control):
    def __init__(self, name, cost, parent = None):
        super().__init__(name=name, cost = 'cost', parent = parent)

    def _actuate(self, state):
        return 
        

if __name__ == '__main__':
    control = TestControl('control', cost = gaussian)
    device = TestDevice('device', parent=control)
    