import time
from emergent.devices import LabJack
from emergent.core import Device
import numpy as np
import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-1]))
import logging as log

class PicoAmp(Device):
    ''' Device driver for the Mirrorcle PicoAmp board. '''
    def __init__(self, name, params = {'labjack': None, 'type': 'digital'}, hub = None):
        ''' Initialize the Device for use. '''
        super().__init__(name, hub = hub, params = params)
        self.addr = {'A': '000', 'B': '001', 'C': '010', 'D': '011', 'ALL': '111'}
        self.labjack = params['labjack']
        assert self.params['type'] in ['digital', 'analog']
        self.add_knob('X')
        self.add_knob('Y')

    def _connect(self):
        ''' Initializes the PicoAmp via SPI. '''
        if self.labjack._connected:
            if self.params['type'] == 'digital':
                self.labjack.spi_initialize(mode=0, CLK = 0, CS = 1, MISO = 3, MOSI = 2)
            self.labjack.PWM(3, 49000, 50)

            if self.params['type'] == 'digital':
                FULL_RESET = '001010000000000000000001'    #2621441
                ENABLE_INTERNAL_REFERENCE =  '001110000000000000000001'     #3670017
                ENABLE_ALL_DAC_CHANNELS = '001000000000000000001111'      #2097167
                ENABLE_SOFTWARE_LDAC = '001100000000000000000001'    #3145728

                self.Vbias = 80.0
                for cmd in [FULL_RESET, ENABLE_INTERNAL_REFERENCE, ENABLE_ALL_DAC_CHANNELS, ENABLE_SOFTWARE_LDAC]:
                    self.command(cmd)
        else:
            log.error('Error: could not initialize PicoAmp - LabJack not connected!')

    def _actuate(self, state):
        ''' Updates MEMS to a target state. Axes not included in the state dict are unaffected.'''
        for axis in state.keys():
            self.setDifferential(state[axis], axis)

    def command(self, cmd):
        ''' Separates the bitstring cmd into a series of bytes and sends them through the SPI. '''
        lst = []
        r = 0
        for i in [0, 8, 16]:
            lst.append(int(cmd[i:8+i],2))
        r = self.labjack.spi_write(lst)

    def digital(self, V):
        ''' Converts an analog voltage V to a 16-bit string for the DAC '''
        Range = 200.0
        Vdigital = V/Range * 65535

        return format(int(Vdigital), '016b')

    def setDifferential(self, V, axis):
        ''' Sets a target differential voltage V=HV_A-HV_B if axis is 'X' or V=HV_C-HV_D if axis is 'Y'.
            For example, if V=2 and  axis is 'X', this sets HV_A=81 and HV_2=79.
            Allowed range of V is -80 to 80.'''
        if self.params['type'] == 'digital':
            V = np.clip(float(V), -80, 80)
            cmdPlus = '00' + '011' + {'X':self.addr['A'], 'Y': self.addr['C']}[axis] + self.digital(self.Vbias+V)
            cmdMinus = '00' + '011' + {'X':self.addr['B'], 'Y': self.addr['D']}[axis] + self.digital(self.Vbias-V)
            self.command(cmdPlus)
            self.command(cmdMinus)
        else:
            V = np.clip(float(V),-5,5)
            channel = {'X':0, 'Y':1}[axis]
            self.labjack.AOut(channel, V, TDAC=True)
