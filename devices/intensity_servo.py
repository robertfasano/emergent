from emergent.archetypes.node import Device

class IntensityServo(Device):
    ''' Device driver for the NIST OFM intensity servo. Designed to control a
        single channel of the board using both outputs of a LabJack LJTick-DAC. '''
    def __init__(self, name, labjack, setpoint_channel, lock_channel, parent = None):
        super().__init__(name, parent = parent)
        self.labjack = labjack
        self.setpoint_channel = setpoint_channel
        self.lock_channel = lock_channel

    def _actuate(state):
        ''' Sets setpoint via analog out control.

            Args:
                state (dict): State dict of the form {'V':1}
        '''
        self.labjack.AOut(self.setpoint_channel, state['V'], HV=True)

    def gain(self, state):
        ''' Turns the gain on or off.

            Args:
                state (int): 0 or 1
        '''
        self.labjack.AOut(self.lock_channel, state*3.3, HV=True)
