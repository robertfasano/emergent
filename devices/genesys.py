import sys
sys.path.append('O:\\Public\\Yb clock')
sys.path.append('C:\\Users\yblab\Documents\GitHub')
from labAPI.protocols.serial import Serial
import serial


class Genesys():
    def __init__(self, port = 'COM13'):
        self.addr = 6
        self.serial = Serial(port = port, baudrate = 19200, encoding = 'ascii', parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS, timeout = 1)
        
        self.command('ADR %i'%self.addr)
        self.command('RST')
        self.command('OUT 1')
        self.set_voltage(6)
        
    def command(self, cmd):      
        reply = self.serial.command(cmd)
        return reply
    
    def set_current(self, I):
        return self.command('PC %f'%I)
    
    def set_voltage(self, V):
        return self.command('PV %f'%V)
    
if __name__ == '__main__':
    p = Genesys()


