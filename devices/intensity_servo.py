from emergent.archetypes.node import Device

class IntensityServo(Device):
    def __init__(self, name, labjack, parent = None):
        super().__init__(name, parent = parent)
        self.labjack = labjack

    def set(self, setpoint, value):

    def select(self, setpoint):

    def toggle(self):
