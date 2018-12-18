from emergent.modules import Thing

class TemplateThing(Thing):
    def __init__(self, name, parent = None):
        Thing.__init__(self, name = name, parent = parent)
        self.add_input('X')         # add some Input nodes
        self.add_input('Y')
        self._connected = self._connect()

    def _connect(self):
        # establish a connection with the thing here
        return 1

    def _actuate(self, state):
        # move to the specified position here
        return
