from emergent.core import Device
import bristol671

class Wavemeter(Device):
    def __init__(self, addr, name = 'Wavemeter', hub = None):


        super().__init__(name=name, hub = hub)
        self.addr = addr

    def _connect(self):
        self.client = bristol671.BristolWM(self.addr)

    def frequency(self):
        return self.client.frequency()*1000
