import sys
sys.path.append('O:\\Public\\Yb clock')
sys.path.append('C:\\Users\yblab\Documents\GitHub')
from labAPI.protocols.serial import Serial, PARITY_NONE, STOPBITS_ONE, EIGHTBITS
from labAPI.archetypes.device import Device


class Genesys(Device):
    def __init__(self, port = 'COM13', name = 'genesys', connect = True, parent = None):
        super().__init__(name, parent = parent)
        self.port = port
        self.addr = 6
        self._connected = 0
        if connect:
            self._connect()

    def _connect(self):
        self.serial = Serial(port = self.port, baudrate = 19200, encoding = 'ascii', parity = PARITY_NONE, stopbits = STOPBITS_ONE, bytesize = EIGHTBITS, timeout = 1, name = 'TDK Genesys')

        if self.serial._connected:
            self.command('ADR %i'%self.addr)
            self.command('RST')
            self.command('OUT 1')
            self.set_voltage(6)
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

if __name__ == '__main__':
    p = Genesys()
