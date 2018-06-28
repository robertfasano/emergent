import sys
sys.path.append('O:\\Public\\Yb clock')
from labAPI.protocols.serial import Serial, PARITY_NONE, STOPBITS_ONE, EIGHTBITS
import numpy as np
from labAPI.archetypes.device import Device

class NetControls(Device):
    def __init__(self, port = 'COM11', connect = True, base_path = None, parent = None):
        Device.__init__(self, name = 'feedthrough', base_path = base_path, parent = parent)
        self.load('default')
        self.port = port
        self._connected = 0
        if connect:
            self._connect()
            
    def _connect(self):
        self.serial = Serial(port = self.port, baudrate = 38400, encoding = 'ascii', parity = PARITY_NONE, stopbits = STOPBITS_ONE, bytesize = EIGHTBITS, timeout = 1, name = 'NetControls driver')

        if self.serial._connected:
            self._connected = 1
            self.axis = 1
            self.initialize()
            self.zero = self.params['position']['value']       # controller thinks it's at zero when restarted, so move relative to last position
            self.position = self.zero
            self.set_load_error(5000)
            self.set_velocity(10000)
        
    def actuate(self, state):
        self.set_position(state[0])
        self.state = state
    def command(self, cmd, val = None, axis = None):
        if val == None:
            val = ''
        if axis == None:
            axis = self.axis
        msg = ':%s%s%s'%(str(self.axis), cmd, val)        
        reply = self.serial.command(msg)
        return reply
    
    def execute_setpoint(self, num):
        return self.command(cmd = 'd', val = num)
                            
    def get_acceleration(self):
        return self.command('a')

    def get_address(self):
        return self.command(cmd='D', axis = 0)
    
    def get_position(self):
        return float(self.command('p').split('p')[1].split('\r')[0])/1e4

    def get_velocity(self):
        return self.command('v')
    
    def halt(self, kind='soft'):
        return self.command(cmd = 'h', val = {'hard':1, 'soft':2}[kind])
    
    def initialize(self):
        return self.command('i', val = 1)
    
    def jog(self, steps):
        return self.command(cmd = 'j', val = steps)
    
    def read_position(self):
        with open('netcontrols_position.txt', 'r') as file:
            pos = float(file.readline())
        self.zero = pos
            
    def save_position(self, pos):
        with open('netcontrols_position.txt', 'w') as file:
            file.write(str(pos+self.zero))
            
    def set_acceleration(self, acc):
        return self.command(cmd = 'a', val = acc)
    
    def set_baudrate(self, baud):
        return self.command(cmd = '%B', val = baud)
    
    def set_load_error(self, error = 32):
        return self.command(cmd = 'L', val = error)
    
    def set_position(self, pos):
#        print('Current position:', self.position - self.zero)
        pos -= self.zero
        pos = np.min([pos, 75])
        np.max([pos, 0])
#        print('Moving to:', pos)
        pos *= 10**4

        self.command(cmd = 'p', val = pos)
        self.wait_until_stopped()
        self.position = self.get_position()
        self.save_position(self.position)
        self.params['position']['value'] = (pos / 10**4)+self.zero
        self.save(self.setpoint)
        
        return self.position
    
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
    
    def wait_until_stopped(self):
        while True:
            status = self.command('g').split('g')[1].split('\r')[0][1]
            if status == '0':
                return
            
if __name__ == '__main__':
    nc = NetControls(port = 'COM11', base_path = 'O:\\Public\\Yb clock\\portable')


