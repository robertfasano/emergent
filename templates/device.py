from emergent.archetypes.node import Device

class TemplateDevice(Device):
    def __init__(self, name, parent = None):
        Device.__init__(self, name = name, parent = parent)
        self.add_input('X')         # add some Input nodes
        self.add_input('Y')
        self._connected = self._connect()

    def _connect(self):
        # establish a connection with the device here
        return 1

    def _actuate(self, state):
        # move to the specified position here
        return
