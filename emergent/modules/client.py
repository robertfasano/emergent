''' The Client class, along with the Server class in server.py, handles communication
    between remote EMERGENT sessions. When the EMERGENT network is initialized, any
    local hubs are instantiated on the PC and a Client is created for each remote hub.
    Possible network commands include:

    * _connect(): attempts to contact the server and sets self._connected=True if successful
    * actuate(state): tells the target server to call its local cluster's actuate() method
    * echo(msg): sends a command to the server and nominally receives the command back
    * get_network(): requests the current state of a remote cluster
    * get_params(): requests operational parameters from the server
'''
import asyncio
import json
import pickle

class Client():
    def __init__(self, addr, port = 8888):
        self.addr = addr
        self.port = port
        self._connected = False
        self.reconnect_delay = 1

    def __getstate__(self):
        d = {}
        ignore = ['network']
        unpickled = []
        for item in ignore:
            if hasattr(self, item):
                unpickled.append(getattr(self,item))
        for item in self.__dict__:
            if self.__dict__[item] not in unpickled:
                d[item] = self.__dict__[item]
        return d

    def actuate(self, state):
        return asyncio.run(self.send({'op': 'actuate', 'params': state}))[0]

    def connect(self):
        self._connected = asyncio.run(self.send({'op': 'connect'}))[0]['params']

    def echo(self, message):
        message = {'op': 'echo', 'params': message}
        resp = self.send(message)
        return resp

    async def send(self, message):
        loop = asyncio.get_event_loop()
        response = await asyncio.gather(self.tcp_echo_client(message, loop))
        return response

    async def tcp_echo_client(self, message, loop):
        reader, writer = await asyncio.open_connection(self.addr, self.port,
                                                       loop=loop)
        writer.write(json.dumps(message).encode())
        await writer.drain()
        data = await reader.read()
        writer.close()
        return pickle.loads(data)

    def get_network(self):
        return asyncio.run(self.send({'op': 'get_network'}))[0]

    def get_params(self):
        return asyncio.run(self.send({'op': 'get_params'}))[0]


if __name__ == '__main__':
    c = Client()
