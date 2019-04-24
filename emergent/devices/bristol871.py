import socket

class Bristol871:
    def __init__(self, name, hub, params={'addr':'10.199.199.1', 'port': 23}):
        self.addr = params['addr']
        self.port = params['port']

    def _connect(self):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((self.addr, self.port))
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

        if threshold is not None:
            if resp < threshold:
                return None
        return resp

    def _monitor(self, targets=['frequency']):
        state = {}
        if 'frequency' in targets:
            state['frequency'] = self._query(b':READ:FREQ?', threshold=1)
            if state['frequency'] is not None:
                state['frequency'] *= 1000
        if 'power' in targets:
            state['power'] = self._query(b':READ:POWER?')
        if 'wavelength' in targets:
            state['wavelength'] = self._query(b':READ:WAV?')

        return state
