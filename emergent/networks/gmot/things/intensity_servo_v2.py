from emergent.modules import Thing
from emergent.things.labjack import LabJack
import functools
import time
import numpy as np

class IntensityServo(Thing):
    ''' Thing driver for a four-channel intensity servo with an embedded pair of
        LabJack T4 DAQs for hub.

        DAC0: probe TTL for integrator/rf switch
        DAC1: slow/trap TTL for integrator/rf switch
        FIO0: trigger for streaming
        FIO4-7: LJTick-DAC for channel 0-3 setpoints
        AIN0-3: channel 0-3 monitors
    '''
    def __init__(self, name, params = {'devid': None}, parent = None):
        super().__init__(name, parent = parent, params = params)
        self.labjack = LabJack(params={'devid': params['devid']})

        self.add_input('probe')
        # self.add_input('V1')
        self.add_input('slowing')
        self.add_input('trapping')

        self.options['Probe'] = self.probe
        self.options['Load'] = self.load

        # enable MOT and disable probe to start
        self.options['Load']()

    def _actuate(self, state):
        ''' Sets setpoint via analog out hub.

            Args:
                state (dict): State dict of the form {'V1':1, 'V2':2,...}
        '''
        for name in state:
            channel = {'probe': 0, 'slowing': 2, 'trapping': 3}[name]
            self.labjack.AOut(channel, state[name], HV=True)

    def _connect(self):
        return

    def enable(self):
        ''' Switches on rf switches and integrator '''
        # self.labjack.DOut('FIO1', 0)
        self.labjack.AOut(0,0)
        self.labjack.AOut(1,0)

    def disable(self):
        ''' Switches off rf switch and integrator '''
        # self.labjack.DOut('FIO1', 1)
        self.labjack.AOut(0,3.3)
        self.labjack.AOut(1,3.3)

    def load(self):
        self.labjack.AOut(0, 3.3)
        self.labjack.AOut(1, 0)

    def probe(self):
        self.labjack.AOut(0, 0)
        self.labjack.AOut(1, 3.3)

    # def autolock(self, channel, frac = 0.9):
    #     ''' Locks the servo to the specified fraction of the unlocked power. '''
    #     self.lock(channel, 0)
    #     time.sleep(1)
    #     lj = [self.labjack[0], self.labjack[0], self.labjack[1], self.labjack[1]][channel]
    #     ch = [0, 1, 0, 1][channel]
    #     unlocked_power = lj.AIn(ch)
    #     # self._actuate({'V%i'%channel:frac*unlocked_power})
    #     state = {self.name: {'V%i'%channel:frac*unlocked_power}}
    #     self.parent.actuate(state)
    #     self.lock(channel, 1)

    # def wave(self, channel, frequency = 1):
    #     ''' Switch between 0 and the current setpoint.
    #
    #     Args:
    #         channel (int): 0-3
    #         frequency (float): wave frequency
    #     '''
    #     lj = [self.labjack[0], self.labjack[0], self.labjack[1], self.labjack[1]][channel]
    #     ch = [0, 1, 0, 1][channel]
    #     sequence = {}
    #     stream = {}
    #     V = self.state['V%i'%channel]
    #     seq = np.array([[0,0], [1/frequency/2,V]])
    #
    #     seq = np.atleast_2d([0, V]).T
    #     stream, scanRate = lj.resample(seq, 1/frequency)
    #     # stream, scanRate = lj.sequence2stream(seq, 1/frequency, 1)
    #     lj.stream_out([ch], stream, scanRate, loop = True)
