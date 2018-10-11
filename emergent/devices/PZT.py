from emergent.devices.labjackT7 import LabJack
from emergent.archetypes.node import Device

class PZT(Device):
    def __init__(self, params, name = 'PZT', parent = None):
        super().__init__(name=name, parent = parent)
        self.labjack = LabJack(devid=params['devid'])
        self.add_input('voltage')

    def _connect(self):
        return 1

    def _actuate(self, state):
        self.labjack.AOut(0,state['voltage'])

    def lock(self, state):
        return

    def get_cavity_transmission(self):
        return self.labjack.AIn(0)

    def get_servo_output(self):
        return self.labjack.AIn(1)
        
if __name__ == '__main__':
    params = {'devid':'440010635'}
