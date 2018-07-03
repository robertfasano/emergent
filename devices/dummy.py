''' A dummy device solely for testing the Lab of Things architecture. '''
import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-2]))
from labAPI.archetypes.device import Device

class Dummy(Device):
    def __init__(self, name = 'dummy', connect = False, parent = None):
        super().__init__(name='dummy', parent = parent)
        self._connected = 0
        if connect:
            self._connect()

    def _connect(self):
        self._connected = 1

    def _actuate(self, state):
        self.state = state

if __name__ == '__main__':
    dummy = Dummy(connect=True)
