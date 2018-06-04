import sys
sys.path.append('O:\Public\Yb clock')
from labAPI.protocols import serial
import serial as s
import struct

class RGA():
    def __init__(self):
        self.serial = serial.Serial(port = 'COM1', baudrate = 28800, parity = s.PARITY_NONE, stopbits = s.STOPBITS_TWO, bytesize = s.EIGHTBITS, timeout = 1, encoding = 'ascii')
        
    def analog_scan(self):
        for command in ['MI1', 'MF100', 'FL1.0', 'NF4', 'SA10']:
            self.serial.command(command)
            
        self.serial.ser.write('SC1'.encode('ascii'))
        reply = ''
        while True:
            r = self.serial.ser.readline().decode()
            reply += r
            print(reply)
            
        return r
        
    def get_pressure(self):
        rga.serial.command('HV0')
        r = rga.serial.command('TP?', decode=False)
#        r = ''.join( [ "%02X " % ord( x ) for x in r ] ).strip()
        r = [str(r[0]), str(r[1]), str(r[2]), str(r[3])]
        

if __name__ == '__main__':
    rga = RGA()
    
#    scan = rga.analog_scan()
        