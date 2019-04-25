from emergent.protocols.serial import Serial, PARITY_NONE, STOPBITS_ONE, EIGHTBITS
import numpy as np
from emergent.core import Device, Knob

class NetControls(Device):
    position = Knob('position')

    def __init__(self, name, hub = None, port = 'COM7'):
        Device.__init__(self, name = name, hub = hub, params = params)
        self.port = port

    def _connect(self):
        self.serial = self._open_serial(port=self.port,
                                        baudrate=38400)
        if self.serial._connected:
            self.axis = 1
            self._initialize()
            self.zero = self.hub.state[self.name]['Z']
            self._set_load_error(5000)
            self.set_velocity(10000)
            return 1

    @position.command
    def position(self, z):
        z = np.clip(z, 0, 100)
        z -= self.zero
        z *= 10**4
        r = self.command(cmd = 'p', val = int(z))
        self._wait_until_stopped()

    @position.query
    def position(self):
        return float(self.command('p').split('p')[1].split('\r')[0])/1e4

    def command(self, cmd, val = None, axis = None):
        if val == None:
            val = ''
        if axis == None:
            axis = self.axis
        msg = ':%s%s%s'%(str(self.axis), cmd, val)
        reply = self.serial.command(msg)
        return reply

    def get_acceleration(self):
        return self.command('a')

    def _get_address(self):
        return self.command(cmd='D', axis = 0)

    def get_velocity(self):
        return self.command('v')

    def halt(self, kind='soft'):
        return self.command(cmd = 'h', val = {'hard':1, 'soft':2}[kind])

    def _initialize(self):
        return self.command('i', val = 1)

    def set_acceleration(self, acc):
        return self.command(cmd = 'a', val = acc)

    def _set_load_error(self, error = 32):
        return self.command(cmd = 'L', val = error)

    def set_velocity(self, vel):
        return self.command(cmd = 'v', val = vel)

    def set_zero(self):
        return self.command('F')

    def _wait_until_stopped(self):
        while True:
            status = self.command('g').split('g')[1].split('\r')[0][1]
            if status == '0':
                return
