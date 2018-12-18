from emergent.modules.node import Thing
import numpy as np

class Loader(Thing):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.add_input('probe delay')
        self.add_input('loading time')
        self.add_input('probe time')
        self.add_input('gate time')
        self.add_input('AOM delay')
    def _actuate(self, state):
        return

    def _connect(self):
        return 1
