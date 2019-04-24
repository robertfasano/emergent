import socket
from emergent.core import Device
import numpy as np

class DLCPro(Device):
    def __init__(self, name, hub, params={'addr': '169.254.120.100'}):
        super().__init__(name, hub)
        self.addr = params['addr']
        self.add_knob('current')
        self.add_knob('piezo')

        self.bounds = {'piezo': (0, 140), 'current': (110, 135)}

    def _connect(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.addr, 1998))
        for i in range(8):
            self.client.recv(4096)

    def _actuate(self, state):
        for key in state:
            state[key] = np.clip(state[key], *self.bounds[key])

        if 'current' in state:
            self.client.sendall(b"(param-set! 'laser1:dl:cc:current-set %f)\n"%state['current'])
            for i in range(3):
                self.client.recv(2)

        if 'piezo' in state:
            self.client.sendall(b"(param-set! 'laser1:dl:pc:voltage-set %f)\n"%state['piezo'])
            for i in range(3):
                self.client.recv(2)

    def _monitor(self):
        state = {}
        self.client.sendall(b"(param-ref 'laser1:dl:cc:current-set)\n")
        state['current'] = float(str(self.client.recv(4096), 'utf-8').split('\n')[0])
        for i in range(2):
            self.client.recv(2)

        self.client.sendall(b"(param-ref 'laser1:dl:pc:voltage-set)\n")
        state['voltage'] = float(str(self.client.recv(4096), 'utf-8').split('\n')[0])
        for i in range(2):
            self.client.recv(2)
        return state
