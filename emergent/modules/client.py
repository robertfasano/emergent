import asyncio
import json
import pickle
from emergent.modules import ProcessHandler
import time

class Client(ProcessHandler):
    def __init__(self, addr, port = 8888):
        ProcessHandler.__init__(self)
        self.addr = addr
        self.port = port
        self._connected = False
        self.reconnect_delay = 1

    def actuate(self, state):
        return asyncio.run(self.send({'op': 'actuate', 'params': state}))[0]

    def connect(self):
        # while not self._connected and not stopped():
        self._connected = asyncio.run(self.send({'op': 'connect'}))[0]['params']
        # time.sleep(self.reconnect_delay)

    def echo(self, message):
        message = {'op': 'echo', 'params': message}
        resp = self.send(message)
        return resp

    async def send(self, message):
        loop = asyncio.get_event_loop()
        # response = loop.run_until_complete(self.tcp_echo_client(message, loop))
        response = await asyncio.gather(self.tcp_echo_client(message, loop))
        return response

    async def tcp_echo_client(self, message, loop):
        reader, writer = await asyncio.open_connection(self.addr, self.port,
                                                       loop=loop)
        writer.write(json.dumps(message).encode())
        await writer.drain()
        data = await reader.read()
        writer.close()
        # await writer.wait_closed()
        return pickle.loads(data)
        # return json.loads(data.decode())

    def get_network(self):
        return asyncio.run(self.send({'op': 'get_network'}))[0]

    def get_params(self):
        return asyncio.run(self.send({'op': 'get_params'}))[0]


if __name__ == '__main__':
    c = Client()
