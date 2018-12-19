import asyncio
import json
from emergent.modules import Hub
from threading import Thread
import logging as log
import pickle

class Server():
    ''' Allows decentralized data viewing via asynchronous communications between the EMERGENT
        master and a remote client. '''

    def __init__(self, network):
        ''' Sets up a new thread for serving. '''
        self.network = network
        self.params = {'tick': 500}
        self.loop = asyncio.get_event_loop()
        self.addr = self.network.get_address()
        self.port = 8888
        coro = asyncio.start_server(self.handle_command, self.addr, self.port, loop=self.loop)
        self.server = self.loop.run_until_complete(coro)
        log.info('Serving on {}'.format(self.server.sockets[0].getsockname()))
        thread = Thread(target=self.start)
        thread.start()

    async def actuate(self, state, reader, writer):
        self.network.actuate(state)
        await self.send({'op': 'update', 'params': 'ok'}, reader, writer)

    def start(self):
        self.loop.run_forever()

    async def send(self, msg, reader, writer):
        resp = pickle.dumps(msg)
        writer.write(resp)
        await writer.drain()
        writer.close()

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



    async def add_listener(self, reader, writer):
        log.info('New listener at %s on port %i.'%(self.addr, self.port))
        await self.send({'op': 'ok'}, reader, writer)
