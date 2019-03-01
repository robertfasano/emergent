from emergent.modules import Thing
import bristol671

class Wavemeter(Thing):
    def __init__(self, addr, name = 'Wavemeter', parent = None):


        super().__init__(name=name, parent = parent)
        self.addr = addr

    def _connect(self):
        self.client = bristol671.BristolWM(self.addr)

    def frequency(self):
        return self.client.frequency()*1000
