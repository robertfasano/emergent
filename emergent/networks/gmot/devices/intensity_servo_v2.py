from emergent.core import Device, Knob
from emergent.devices.labjack import LabJack
import functools
import time
import numpy as np

class IntensityServo(Device):
    ''' Device driver for a four-channel intensity servo with an embedded pair of
        LabJack T4 DAQs for hub.

        DAC0: probe TTL for integrator/rf switch
        DAC1: slow/trap TTL for integrator/rf switch
        FIO0: trigger for streaming
        FIO4-7: LJTick-DAC for channel 0-3 setpoints
        AIN0-3: channel 0-3 monitors
    '''
    probe = Knob('probe')
    slowing = Knob('slowing')
    trapping = Knob('trapping')

    def __init__(self, name, hub = None, devid=''):
        super().__init__(name, hub = hub)
        self.labjack = LabJack(params={'devid': devid})

    @probe.command
    def probe(self, V):
        self.labjack.AOut(0, V, TDAC=True)

    @probe.query
    def probe(self):
        self.labjack.AIn(0)

    @slowing.command
    def slowing(self, V):
        self.labjack.AOut(2, V, TDAC=True)

    @slowing.query
    def slowing(self):
        self.labjack.AIn(2)

    @trapping.command
    def trapping(self, V):
        self.labjack.AOut(3, V, TDAC=True)

    @trapping.query
    def trapping(self):
        self.labjack.AIn(3)

    def enable(self):
        ''' Switches on rf switches and integrator '''
        self.labjack.AOut(0,0)
        self.labjack.AOut(1,0)

    def disable(self):
        ''' Switches off rf switch and integrator '''
        self.labjack.AOut(0,3.3)
        self.labjack.AOut(1,3.3)
