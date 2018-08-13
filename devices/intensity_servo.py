from archetypes.node import Device
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
        func_description = 'Toggle integrator'
        func = functools.partial(self.lock, 1-self.integrator)

        self.options = {func_description:func}

        self.add_input('V')

    def _actuate(self, state):
        ''' Sets setpoint via analog out control.

            Args:
                state (dict): State dict of the form {'V':1}
        '''
        self.labjack.AOut(self.setpoint_channel, state['V'])

    def lock(self, state):
        ''' Turns the integrator on or off. Digital high = off.

            Args:
                state (int): 0 or 1
        '''
        self.integrator = state
        self.labjack.AOut(self.lock_channel, (1-state)*3.3)

    def autolock(self, frac = 0.9):
        ''' Locks the servo to the specified fraction of the unlocked power. '''
        self.lock(0)
        time.sleep(1)
        unlocked_power = self.labjack.AIn(0)
        self._actuate({'V':frac*unlocked_power})
        self.lock(1)

    def wave(self, frequency = 1):
        ''' Switch between 0 and the current setpoint. '''
        sequence = {}
        stream = {}
        V = self.state['V']
        seq = [[0,0], [1/frequency/2,V]]
        stream, scanRate = self.labjack.sequence2stream(seq, 1/frequency, 1)
        self.labjack.stream_out([self.setpoint_channel], stream, scanRate, loop = True)
