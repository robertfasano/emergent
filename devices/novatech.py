import serial
import sys
sys.path.append('O:/Public/Yb clock/')
from labAPI.protocols.serial import Serial
import serial


class Novatech():
    def __init__(self, port = 'COM7'):
        self.serial = Serial(
                port=port,
                baudrate=19200,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout = 1,
                encoding = 'ascii'
            )
    
    def set_amplitude(self,ch, V):
        return self.serial.command('V%i %i'%(ch, V))
        
    def set_frequency(self,ch, f):
        ''' Args:
                int ch
                str f
                '''
        return self.serial.command('f%i %s'%(ch, f))
    
if __name__ == '__main__':
    n = Novatech(port='COM19')
    n.set_frequency(3,115)
    n.set_amplitude(3,475)