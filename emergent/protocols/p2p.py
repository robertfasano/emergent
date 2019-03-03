''' This module handles communications between EMERGENT sessions on remote
    networked PCs through a symmetric client/server protocol. '''

import asyncio
import json
from threading import Thread
import logging as log
import pickle

import decorator

@decorator.decorator
def thread(func, *args, **kwargs):
    new_thread = Thread(target=func, args=args, kwargs=kwargs)
    new_thread.start()


class Sender():
    def __init__(self, name=None, addr=None, port=None):
        self.name = name
        self.addr = addr
        if self.addr is None:
            self.addr = '127.0.0.1'
        self.port = port
        if self.port is None:
            self.port = 80305
        self._connected = False

    @thread
    def connect(self):
        ''' Initialize a connection with the server. '''
        print('%s:'%self.name, 'Opening connection to %s::%i.'%(self.addr, self.port))
        self._connected = asyncio.run(self._send({'op': 'connect'}))['params']

    @thread
    def echo(self, message):
        ''' Client/server echo for debugging '''
        message = {'op': 'echo', 'params': message}
        reply = asyncio.run(self._send(message))
        print('%s:'%self.name, 'Received:', reply)
    async def _send(self, message):
        loop = asyncio.get_event_loop()
        print('%s:'%self.name, 'Sending:', message)
        reader, writer = await asyncio.open_connection(self.addr, self.port,
                                                       loop=loop)
        writer.write(json.dumps(message).encode())
        await writer.drain()
        data = await reader.read()
        writer.close()
        return pickle.loads(data)


class Listener():
    def __init__(self, name = None, addr = 'localhost', port = 29170):
        ''' Sets up a new thread for serving. '''
        self.name = name
        print('%s:'%self.name, 'Serving at %s::%i.'%(addr, port))
        self.addr = addr
        self.port = port
        self.start()

    @thread
    def start(self):
        ''' Start the server. '''
        self.loop = asyncio.new_event_loop()
        coro = asyncio.start_server(self.handle_command, self.addr, self.port, loop=self.loop)
        self.loop.run_until_complete(coro)
        self.loop.run_forever()

    async def send(self, msg, writer):
        ''' Sends a message asynchronously to the client. '''
        resp = pickle.dumps(msg)
        writer.write(resp)
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def handle_command(self, reader, writer):
        ''' Intercepts and reacts to a message from the client. '''
        data = await reader.read(100)
        message = json.loads(data.decode())

        print('%s:'%self.name, 'Received:', message)
        op = message['op']
        if op == 'connect':
            log.info('New listener at %s on port %i.', self.addr, self.port)
            await self.send({'op': 'update', 'params': 1}, writer)
        if op == 'echo':
            await self.send({'op': 'echo', 'params': message['params']}, writer)

class P2PNode():
    def __init__(self, name=None, addr = 'localhost', port = 29170):
        ''' Sets up a Listener on the passed address and port. '''
        self.name=name
        self.listener = Listener(name, addr, port)

    def bind(self, addr = 'localhost', port = 29171):
        self.sender = Sender(self.name, addr, port)
        self._connected = self.sender.connect()


if __name__ == '__main__':
    n0 = P2PNode('localhost', 29170)
    n1 = P2PNode('localhost', 29171)

    n0.bind('localhost', 29171)
    n1.bind('localhost', 29170)
