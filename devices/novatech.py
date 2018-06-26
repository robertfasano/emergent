import serial
import sys
sys.path.append('O:/Public/Yb clock/')
from labAPI.protocols.serial import Serial
from labAPI.archetypes.device import Device

class Novatech(Device):
    def __init__(self, port = 'COM7', connect = True):
        super().__init__(name='novatech')
        self.port = port
        self._connected = 0
        if connect:
            self._connect()
            
    def _connect(self):
        self.serial = Serial(
                port=self.port,
                baudrate=19200,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout = 1,
                encoding = 'ascii',
                name = 'Novatech DDS'
            )
        if self.serial._connected:
            self._connected = 1
    
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