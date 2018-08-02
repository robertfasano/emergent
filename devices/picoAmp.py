'''if the amplifiers are not working, then first unplug and reinsert the #1 +5V HV the pin once it is connected
and initialized; otherwise, ensure that 5 volts of power are being delivered to the board'''
import time
from emergent.devices.labjackT7 import LabJack
from emergent.archetypes.node import Device
import numpy as np
import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-1]))

class PicoAmp(Device):
    def __init__(self, name, labjack, parent = None):
        super.__init__(self, name, parent = parent)
        self.addr = {'A': '000', 'B': '001', 'C': '010', 'D': '011', 'ALL': '111'}
        self.labjack = labjack
        
        self.add_input('X')
        self.add_input('Y')

    def _connect(self):
        if self.labjack._connected:
            self.labjack.spi_initialize(mode=0, CLK = 0, CS = 1, MISO = 3, MOSI = 2)
            self._initialize()
            self.actuate(self.state)

    def _initialize(self):
        ''' Initializes the DAC and sets the bias voltage on all four channels to 80 V. '''
        self.labjack.PWM(3, 49000, 50)

        FULL_RESET = '001010000000000000000001'    #2621441
        ENABLE_INTERNAL_REFERENCE =  '001110000000000000000001'     #3670017
        ENABLE_ALL_DAC_CHANNELS = '001000000000000000001111'      #2097167
        ENABLE_SOFTWARE_LDAC = '001100000000000000000001'    #3145728

        for cmd in [FULL_RESET, ENABLE_INTERNAL_REFERENCE, ENABLE_ALL_DAC_CHANNELS, ENABLE_SOFTWARE_LDAC]:
            self.command(cmd)

    def _actuate(self, state):
        ''' Updates MEMS to a target state. Axes not included in the state dict are unaffected.'''
        for axis in state.keys():
                state[axis] = np.clip(state[axis], self.min, self.max)
                self.setDifferential(state[axis], axis)
        self.state = state

    def command(self, cmd):
        ''' Separates the bitstring cmd into a series of bytes and sends them through the SPI. '''
        lst = []
        r = 0
        for i in [0, 8, 16]:
            lst.append(int(cmd[i:8+i],2))
        r = self.labjack.spi_write(lst, verbose = False)

    def digital(self, V):
        ''' Converts an analog voltage V to a 16-bit string for the DAC '''
        Range = 200.0
        Vdigital = V/Range * 65535

        return format(int(Vdigital), '016b')

    def readADC(self, num = 1, delay = 0):
        time.sleep(delay)
        return self.labjack.AIn(0, num=num)

    def setDifferential(self, V, axis):
        ''' Sets a target differential voltage V=HV_A-HV_B if axis is 'X' or V=HV_C-HV_D if axis is 'Y'.
            For example, if V=2 and  axis is 'X', this sets HV_A=81 and HV_2=79.
            Allowed range of V is -80 to 80.'''
        V = np.clip(float(V), -80, 80)
        cmdPlus = '00' + '011' + {'X':self.addr['A'], 'Y': self.addr['C']}[axis] + self.digital(self.Vbias+V)
        cmdMinus = '00' + '011' + {'X':self.addr['B'], 'Y': self.addr['D']}[axis] + self.digital(self.Vbias-V)

        self.command(cmdPlus)
        self.command(cmdMinus)

if __name__ == '__main__':
    import sys
    sys.path.append('O:/Public/Yb clock')
    pico = PicoAmp(lowlevel = False)
    pico.squareWave(80,2)     # aligned for differential amplitude of 80 V
