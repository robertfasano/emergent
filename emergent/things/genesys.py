import sys
sys.path.append('O:\\Public\\Yb clock')
sys.path.append('C:\\Users\yblab\Documents\GitHub')
from emergent.protocols.serial import Serial, PARITY_NONE, STOPBITS_ONE, EIGHTBITS
from emergent.modules import Thing
import time

class Genesys(Thing):
    ''' Thing driver for the TDK Genesys programmable power supply. '''
    def __init__(self, name, port, parent = None):
        if parent:
            super().__init__(name, parent = parent)
        self.port = port
        self.addr = 6
        self._connected = 0

        # self._connect()

    def _connect(self):
        ''' Establish a serial connection over USB and enable output. '''
        self.serial = Serial(port = self.port, baudrate = 19200,
                             encoding = 'ascii', parity = PARITY_NONE,
                             stopbits = STOPBITS_ONE, bytesize = EIGHTBITS,
                             timeout = 1, name = 'TDK Genesys')

        if self.serial._connected:
            self.command('ADR %i'%self.addr)
            self.command('RST')
            self.command('OUT 1')
            self._connected = 1

    def _actuate(self, state):
        self.set_current(state[0])

    def command(self, cmd):
        reply = self.serial.command(cmd)
        return reply

    def set_current(self, I):
        return self.command('PC %f'%I)

    def set_voltage(self, V):
        return self.command('PV %f'%V)

    def wave(self, frequency, stopped = None):
        I0 = self.state[0]
        i = 0
        while not stopped():
            i = (i+1) % 2
            self.set_current(I0*i)
            time.sleep(1/frequency)
        self.set_current(I0)


if __name__ == '__main__':
    p = Genesys(lowlevel = False)
    try:
        p.set_current(20)
        time.sleep(5)
        p.set_current(0)
    finally:
        p.serial.close()
