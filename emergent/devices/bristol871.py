from emergent.core import Device, Sensor

class Bristol871(Device):
    frequency = Sensor('frequency')
    power = Sensor('power')

    def __init__(self, name, hub, params={'addr':'10.199.199.1', 'port': 23}):
        super().__init__(name, hub, params)
        self.addr = params['addr']
        self.port = params['port']

    def _connect(self):
        try:
            self.client = self._open_tcpip(self.addr, self.port)
            for i in range(2):
                self.client.recv(4096)
        except Exception as e:
            print(e)
            self._connected = 0
            return
        self._connected = 1

    def _query(self, msg, threshold = None):
        self.client.sendall(b'%s\n'%msg)
        resp = float(str(self.client.recv(1024), 'utf-8').split('\r')[0])

        return resp

    @frequency.query
    def frequency(self):
        f = self._query(b':READ:FREQ?')
        if f < 1e-3:          # detect read failures and return None
            return None
        else:
            return f * 1000   # return frequency in GHz

    @power.query
    def power(self):
        return self._query(b':READ:POWER?')
