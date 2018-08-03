from archetypes.node import Device
from utility import dev

@dev 
class TestDevice(Device):
        def __init__(self, name, parent):
                super().__init__(name, parent)
                self.add_input('X')
                self.add_input('Y')
        def _actuate(self, state):
                print(state)
