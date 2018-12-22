''' The Server class, along with the Client class in client.py, handles communication
    between remote EMERGENT sessions. When the EMERGENT network is initialized, all
    PCs in the session create a server to handle the following client commands:

    * _connect(): attempts to contact the server and sets self._connected=True if successful
    * actuate(state): tells the target server to call its local cluster's actuate() method
    * echo(msg): sends a command to the server and nominally receives the command back
    * get_network(): requests the current state of a remote cluster
    * get_params(): requests operational parameters from the server
'''

import asyncio
import json
from emergent.modules import Hub
from threading import Thread
import logging as log
import pickle
from emergent.utility import get_address

class Server():
    ''' Allows decentralized data viewing via asynchronous communications between the EMERGENT
        master and a remote client. '''

    def __init__(self, network):
        ''' Sets up a new thread for serving. '''
        self.network = network
        self.params = {'tick': 500}
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        if self.network.addr is None:
            self.addr = get_address()
        else:
            self.addr = self.network.addr
        self.port = self.network.port

        coro = asyncio.start_server(self.handle_command, self.addr, self.port, loop=self.loop)
        self.server = self.loop.run_until_complete(coro)

        thread = Thread(target=self.start)
        thread.start()

    async def actuate(self, state, reader, writer):
        self.network.actuate(state)
        await self.send({'op': 'update', 'params': 1}, reader, writer)

    async def echo(self, message, reader, writer):
        await self.send(message, reader, writer)

    def start(self):
        self.loop.run_forever()

    async def send(self, msg, reader, writer):
        resp = pickle.dumps(msg)
        writer.write(resp)
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def handle_command(self, reader, writer):
        data = await reader.read(100)
        addr = writer.get_extra_info('peername')
        message = json.loads(data.decode())
        op = message['op']

        if 'get' in op:
            var = getattr(self, op.split('_')[1])
            await self.send(var, reader, writer)
        elif op == 'connect':
            await self.add_listener(reader, writer)
        elif op == 'actuate':
            await self.actuate(message['params'], reader, writer)
        elif op == 'echo':
            await self.echo(message['params'], reader, writer)


    async def add_listener(self, reader, writer):
        log.info('New listener at %s on port %i.'%(self.addr, self.port))
        await self.send({'op': 'update', 'params': 1}, reader, writer)
