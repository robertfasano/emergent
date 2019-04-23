from emergent.devices.labjack import LabJack
from emergent.core import Device

class PZT(Device):
    def __init__(self, params, name = 'PZT', hub = None):
        super().__init__(name=name, hub = hub)
        self.labjack = LabJack(params=params)
        self.add_knob('voltage')
        self.options['Toggle lock'] = self.toggle_lock
        self.lock(0)

    def _connect(self):
        return 1

    def _actuate(self, state):
        self.labjack.AOut(4,state['voltage'], TDAC=True)

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
    lj = LabJack(params=params)
