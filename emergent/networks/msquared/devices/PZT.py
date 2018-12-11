from emergent.devices.labjackT7 import LabJack
from emergent.archetypes import Device

class PZT(Device):
    def __init__(self, params, name = 'PZT', parent = None):
        super().__init__(name=name, parent = parent)
        self.labjack = LabJack(devid=params['devid'])
        self.add_input('voltage')
        self.options['Toggle lock'] = self.toggle_lock
        self.lock(0)

    def _connect(self):
        return 1

    def _actuate(self, state):
        self.labjack.AOut(4,state['voltage'], HV=True)

    def lock(self, state):
        self.lock_state = state
        self.labjack.DOut(6,1-state)

    def toggle_lock(self):
        self.lock(1-self.lock_state)

    def get_cavity_transmission(self):
        return self.labjack.AIn(0)

    def get_servo_output(self):
        return self.labjack.AIn(1)

if __name__ == '__main__':
    params = {'devid':'440010635'}
