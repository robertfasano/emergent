from emergent.core import Device, Knob

class DLCPro(Device):
    piezo = Knob('piezo')
    current = Knob('current')

    def __init__(self, name, hub, params={'addr': '169.254.120.100'}):
        super().__init__(name, hub)
        self.addr = params['addr']

    def _connect(self):
        self.client = self._open_tcpip(self.addr, 1998)
        for i in range(8):
            r=self.client.recv(4096)

    @piezo.command
    def piezo(self, V):
        self.client.sendall(b"(param-set! 'laser1:dl:pc:voltage-set %f)\n"%V)
        for i in range(3):
            self.client.recv(2)

    @current.command
    def current(self, I):
        self.client.sendall(b"(param-set! 'laser1:dl:cc:current-set %f)\n"%I)
        for i in range(3):
            self.client.recv(2)

    @piezo.query
    def piezo(self):
        self.client.sendall(b"(param-ref 'laser1:dl:pc:voltage-set)\n")
        V = float(str(self.client.recv(4096), 'utf-8').split('\n')[0])
        for i in range(2):
            self.client.recv(2)
        return V

    @current.query
    def current(self):
        self.client.sendall(b"(param-ref 'laser1:dl:cc:current-set)\n")
        I = float(str(self.client.recv(4096), 'utf-8').split('\n')[0])
        for i in range(2):
            self.client.recv(2)
        return I
