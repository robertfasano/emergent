from emergent.archetypes.node import Device
from emergent.devices.labjackT7 import LabJack
import functools
import time
import numpy as np
class IntensityServo(Device):
    ''' Device driver for a four-channel intensity servo with an embedded pair of
        LabJack T4 DAQs for control.

        LJ0 DAC0/1: channel 1/2 setpoint
        LJ0 FIO6/7: channel 1/2 on/off

        LJ1 DAC0/1: channel 3/4 setpoint
        LJ1 FIO6/7: channel 3/4 on/off
    '''
    def __init__(self, name, id1, id2, parent = None):
        super().__init__(name, parent = parent)
        self.labjack = []
        self.labjack.append(None)
        # self.labjack.append(LabJack(devid=id1))
        self.labjack.append(LabJack(devid=id2))

        # for ch in [0,1,2,3]:
        for ch in [2,3]:
            self.lock(ch, 0)

        # self.add_input('V0')
        # self.add_input('V1')
        self.add_input('V2')
        self.add_input('V3')

    def _actuate(self, state):
        ''' Sets setpoint via analog out control.

            Args:
                state (dict): State dict of the form {'V1':1, 'V2':2,...}
        '''
        for name in state:
            channel = int(name[1])
            lj = [self.labjack[0], self.labjack[0], self.labjack[1], self.labjack[1]][channel]
            ch = [0, 1, 0, 1][channel]
            lj.AOut(ch, state[name])

    def _connect(self):
        return
        
    def lock(self, channel, state):
        ''' Turns the integrator on or off. Digital high = off.

            Args:
                channel (int): 0-3
                state (int): 0 or 1
        '''
        lj = [self.labjack[0], self.labjack[0], self.labjack[1], self.labjack[1]][channel]
        ch = [6, 7, 6, 7][channel]
        self.integrator = state
        lj.DOut('FIO%i'%ch, int(1-state))

    def autolock(self, channel, frac = 0.9):
        ''' Locks the servo to the specified fraction of the unlocked power. '''
        self.lock(channel, 0)
        time.sleep(1)
        lj = [self.labjack[0], self.labjack[0], self.labjack[1], self.labjack[1]][channel]
        ch = [0, 1, 0, 1][channel]
        unlocked_power = lj.AIn(ch)
        # self._actuate({'V%i'%channel:frac*unlocked_power})
        state = {self.name: {'V%i'%channel:frac*unlocked_power}}
        self.parent.actuate(state)
        self.lock(channel, 1)

    def wave(self, channel, frequency = 1):
        ''' Switch between 0 and the current setpoint.

        Args:
            channel (int): 0-3
            frequency (float): wave frequency
        '''
        lj = [self.labjack[0], self.labjack[0], self.labjack[1], self.labjack[1]][channel]
        ch = [0, 1, 0, 1][channel]
        sequence = {}
        stream = {}
        V = self.state['V%i'%channel]
        seq = np.array([[0,0], [1/frequency/2,V]])

        seq = np.atleast_2d([0, V]).T
        stream, scanRate = lj.resample(seq, 1/frequency)
        # stream, scanRate = lj.sequence2stream(seq, 1/frequency, 1)
        lj.stream_out([ch], stream, scanRate, loop = True)
