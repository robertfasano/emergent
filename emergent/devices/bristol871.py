from emergent.core import Device, Sensor, Knob

class Bristol871(Device):
    frequency = Sensor('frequency')
    power = Sensor('power')
    sample_rate = Knob('sample_rate')

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
        resp = str(self.client.recv(1024), 'utf-8').split('\r')[0]

        return resp

    def _command(self, msg, threshold = None):
        self.client.sendall(b'%s\n'%msg)


    @frequency.query
    def frequency(self):
        f = float(self._query(b':READ:FREQ?'))
        if f < 1e-3:          # detect read failures and return None
            return None
        else:
            return f * 1000   # return frequency in GHz

    @power.query
    def power(self):
        return float(self._query(b':READ:POWER?'))

    @sample_rate.query
    def sample_rate(self):
        return int(self._query(b':TRIG:SEQ:RATE?'))

    @sample_rate.command
    def sample_rate(self, new_rate):
        return self._command(b':TRIG:SEQ:RATE %i'%new_rate)
