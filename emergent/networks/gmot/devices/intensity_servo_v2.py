from emergent.core import Device, Knob
from labyak import LabDAQ
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

    def __init__(self, name, params={'devid': ''}, hub = None, devid=''):
        super().__init__(name, hub = hub)
        self.labjack = LabDAQ(devid=params['devid'])

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

if __name__ == '__main__':
    servo = IntensityServo('servo', params = {'devid': '470016973'}, hub = None)
    # servo.probe = 1 # set probe setpoint to 1 V
    # servo.trapping = 2 # set trapping setpoint to 2 V
