from toptica.lasersdk.client import Client, NetworkConnection
from emergent.core import Device

class DLCPro(Device):
    def __init__(self, name, hub, params={'addr': '169.254.120.100'}):
        super().__init__(name, hub)
        self.addr = params['addr']
        self.add_knob('piezo')
        self.add_knob('current')

    def _actuate(self, state):
        with Client(NetworkConnection(self.addr)) as client:
            if 'current' in state:
                client.set('laser1:dl:cc:current-set', state['current'])
            if 'piezo' in state:
                client.set('laser1:dl:pc:voltage-set', state['piezo'])

    def _connect(self):
        try:
            with Client(NetworkConnection(self.addr)) as client:
                self.serial_number = client.get('serial-number', str)
        except:
            self._connected = 0
            return
        self._connected = 1

    def _monitor(self):
        ''' Queries the controller and returns the current state dict '''
        with Client(NetworkConnection(self.addr)) as client:
            state = {'current': client.get('laser1:dl:cc:current-set', float),
                     'piezo': client.get('laser1:dl:pc:voltage-set', float)
                    }
        return state

if __name__ == "__main__":
    laser = DLCPro('DLCPro', None, {'addr': '169.254.120.100'})
    laser._connect()
    print(laser._monitor())
