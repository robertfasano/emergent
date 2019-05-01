from emergent.core import Device, Knob
from emergent.utilities.fifo import FIFO
from emergent.utilities.decorators import queue, thread

class DLCPro(Device):
    piezo = Knob('piezo')
    current = Knob('current')
    temperature = Knob('temperature')
    def __init__(self, name, hub, params={'addr': '169.254.120.100'}):
        super().__init__(name, hub)
        self.addr = params['addr']
        self.queue = FIFO()
        self.queue.run()

    def _connect(self):
        self.client = self._open_tcpip(self.addr, 1998)
        for i in range(8):
            r=self.client.recv(4096)

    @queue
    def _command(self, msg):
        self.client.sendall(msg)
        self.drain()

    @queue
    def _query(self, msg):
        self.client.sendall(msg)
        r = self.client.recv(4096)
        resp = str(r, 'utf-8')
        if '>' not in resp:
            self.drain()
        return resp.split('\n')[0]

    def drain(self):
        while True:
            r = str(self.client.recv(16), 'utf-8')
            if '>' in r:
                break


    @piezo.command
    def piezo(self, V):
        self._command(b"(param-set! 'laser1:dl:pc:voltage-set %f)\n"%V)

    @current.command
    def current(self, I):
        self._command(b"(param-set! 'laser1:dl:cc:current-set %f)\n"%I)

    @temperature.command
    def temperature(self, T):
        self._command(b"(param-set! 'laser1:dl:tc:temp-set %f)\n"%T)

    @piezo.query
    def piezo(self):
        return float(self._query(b"(param-ref 'laser1:dl:pc:voltage-set)\n"))

    @current.query
    def current(self):
        return float(self._query(b"(param-ref 'laser1:dl:cc:current-set)\n"))

    @temperature.query
    def temperature(self):
        return float(self._query(b"(param-ref 'laser1:dl:tc:temp-act)\n"))
