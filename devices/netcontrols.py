from labAPI import protocols
import serial


class NetControls():
    def __init__(self):
        self.serial = protocols.serial(port = 'COM1', baudrate = 19200, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS, timeout = 1, encoding = 'ascii')
        self.position = 0
        self.velocity = 0
        self.acceleration = 0
        self.axis = 1
        
    def command(self, cmd, val = None):
        if val == None:
            val = ''
        msg = ':%s%s%s'%(str(self.axis), cmd, val)        
        reply = self.serial.command(msg)
        return reply
    
    def execute_setpoint(self, num):
        return self.command(cmd = 'd', val = num)
                            
    def get_acceleration(self):
        return self.command('a')

    def get_position(self):
        return self.command('p')

    def get_velocity(self):
        return self.command('v')
    
    def halt(self, kind='soft'):
        return self.command(cmd = 'h', val = {'hard':1, 'soft':2}[kind])
    
    def initialize(self):
        return self.command('i')
    
    def jog(self, steps):
        return self.command(cmd = 'j', val = steps)
    
    def set_acceleration(self, acc):
        return self.command(cmd = 'a', val = acc)
    
    def set_baudrate(self, baud):
        return self.command(cmd = '%B', val = baud)
    
    def set_position(self, pos):
        return self.command(cmd = 'p', val = pos)
    
    def set_velocity(self, vel):
        return self.command(cmd = 'v', val = vel)
    
    def set_setpoint(self, num, pos = None):
        ''' Sets the setpoint labeled by num.
        Args: int num (0-9)
              int pos      '''
              
        if pos == None:
            pos = self.position
        return self.command(cmd = num, val = pos)
    
    def set_speed(self, s):
        return self.command(cmd = 's', val = s)
    
    def set_zero(self):
        return self.command('F')
    
feedthrough = NetControls()


