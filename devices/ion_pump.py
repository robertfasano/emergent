import sys
sys.path.append('O:\\Public\\Yb clock')
from labAPI.protocols.serial import Serial
import serial

PORT_NUM = 17 #SET!

class IonPump():
    """ Driver for the Digitel ion pump."""

    def __init__(self, port = PORT_NUM):
        self.port = port
        self.port_str = hex(port)[2::].zfill(2) #format in hex, makes 2 chars
        self.serial = Serial(port = 'COM%d' % port,
                             baudrate = 115200, #leave these vals alone
                             encoding = 'ascii',
                             parity = serial.PARITY_NONE,
                             stopbits = serial.STOPBITS_ONE,
                             bytesize = serial.EIGHTBITS,
                             timeout = 1)

    def _command(self, cmd, cmd_sum):
        """Computes a checksum, formats a message, returns device response."""
        checksum = (192 + cmd_sum + self.port) % 256 #2 factors of 96 for the
                                                   #spaces and for the port num
        checksum = hex(checksum)[2::].zfill(2) #format in hex, makes 2 chars
        msg = '~ %s %s %s' % (self.port_str, cmd, checksum)
        print(msg)
        reply = self.serial.command(msg)
        print(reply)
        return reply

    def read_current(self):
        reply = self._command(cmd = '0A', cmd_sum = 113) #scientific notation str w/ units
        print(reply)
        return float(reply[9:16]) #value in amps

    def read_pressure(self):
        reply = self._command(cmd = '0B', cmd_sum = 114) #scientific notation str w/ units
        return float(reply[9:16]) #value in Torr, unless changed on device

    def read_voltage(self):
        reply =  self._command(cmd = '0C', cmd_sum = 115)
        return int(reply[9:13])#formatted as int, in volts

    def close(self):
        self.serial.close()

if __name__ == '__main__':
    digitel = IonPump(PORT_NUM)
    try:
        print('%s amps'%digitel.read_current())
        print('%s torr'%digitel.read_pressure())
        print('%s volts'%digitel.read_voltage())
    except Exception as e:
        print(e)
        digitel.close()
        print('Serial connection closed')
    
    
    