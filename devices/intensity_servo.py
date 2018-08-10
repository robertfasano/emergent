from emergent.archetypes.node import Device
import functools

class IntensityServo(Device):
    ''' Device driver for the NIST OFM intensity servo. Designed to control a
        single channel of the board using both DAC channels of a LabJack T7. '''
    def __init__(self, name, labjack, setpoint_channel, lock_channel, parent = None):
        super().__init__(name, parent = parent)
        self.labjack = labjack
        self.setpoint_channel = setpoint_channel
        self.lock_channel = lock_channel
        self.lock(0)

        ''' Option to switch gain on/off '''
        other_state = {1:'off', 0:'on'}[self.integrator]
        func_description = 'Turn integrator %s'%other_state
        func = functools.partial(self.lock, 1-self.integrator)

        self.options = {func_description:func}

    def _actuate(state):
        ''' Sets setpoint via analog out control.

            Args:
                state (dict): State dict of the form {'V':1}
        '''
        self.labjack.AOut(self.setpoint_channel, state['V'], HV=True)

    def lock(self, state):
        ''' Turns the integrator on or off. Digital high = off.

            Args:
                state (int): 0 or 1
        '''
        self.integrator = state
        self.labjack.AOut(self.lock_channel, (1-state)*3.3, HV=True)
