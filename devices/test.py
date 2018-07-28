''' A dummy device solely for testing the EMERGENT architecture. '''
import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-1]))
from emergent.archetypes.node import Device, Control

class TestDevice(Device):
        def __init__(self, name, parent):
                super().__init__(name, parent)

        def _actuate(self, state):
                return


