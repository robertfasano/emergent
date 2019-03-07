''' This module handles communications between EMERGENT sessions on remote
    networked PCs through a symmetric client/server protocol. '''

import asyncio
import json
from threading import Thread
import logging as log
import pickle
import time
from emergent.utilities.testing import Timer
import decorator
import datetime

@decorator.decorator
def thread(func, *args, **kwargs):
    new_thread = Thread(target=func, args=args, kwargs=kwargs)
    new_thread.start()

timer = Timer()

def dump(message):
    # return json.dumps(message).encode()
    return pickle.dumps(message)

def load(message):
    return pickle.loads(message)

class Sender():
    def __init__(self, node, name=None, addr=None, port=None):
        self.node = node
        self.name = name
        self.addr = addr
        if self.addr is None:
            self.addr = '127.0.0.1'
        self.port = port
        if self.port is None:
            self.port = 80305
        self._connected = False

        self.loop = None
        self.reader = None

        self.read_size = 10*1024000

    async def _open_connection(self):
        ''' Opens a connection to a remote listener. '''
        self.reader, self.writer = await asyncio.open_connection(self.addr, self.port,
                                                           loop=self.loop, limit=self.read_size)
        params = {'addr': self.addr, 'port': self.node.listener.port}
        self.writer.write(dump({'op': 'connect', 'params': params}))
        await self.writer.drain()
        resp = load(await self.reader.read(100))
        # print(datetime.datetime.now().isoformat(), '%s:'%self.name, 'Received:', resp)
        self.node._connected = resp['params']

    @thread
    def _hold_connection(self):
        ''' Starts an event loop and opens a persistent connection. '''
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        asyncio.ensure_future(self._open_connection(), loop=self.loop)
        self.loop.run_forever()

    def echo(self, message):
        ''' Client/server echo for debugging '''
        message = {'op': 'echo', 'params': message}
        reply = self.send(message)

    def send(self, message):
        message['timestamp'] = datetime.datetime.now().isoformat()
        future = asyncio.run_coroutine_threadsafe(self._send(message), loop=self.loop)
        resp = future.result()
        # print(datetime.datetime.now().isoformat(), '%s:'%self.name, 'Received:', resp)

        return resp

    async def _send(self, message):
        # print(datetime.datetime.now().isoformat(), '%s:'%self.name, 'Sending:', message)
        # self.writer.write(json.dumps(message).encode())
        self.writer.write(dump(message))
        await self.writer.drain()
        data = await self.reader.read(self.read_size)
        return pickle.loads(data)

class Listener():
    def __init__(self, node, name = None, addr = 'localhost', port = 29170):
        ''' Sets up a new thread for serving. '''
        self.node = node
        self.name = name
        # print(datetime.datetime.now().isoformat(), '%s:'%self.name, 'Serving at %s::%i.'%(addr, port))
        self.addr = addr
        self.port = port
        self.read_size = 10*1024000
        self._connected = False
        self.start()

    @thread
    def start(self):
        ''' Start the server. '''
        self.loop = asyncio.new_event_loop()
        coro = asyncio.start_server(self.handle_command, self.addr, self.port, loop=self.loop)
        self.loop.run_until_complete(coro)
        self.loop.run_forever()

    async def confirm(self, writer, success=True):
            reply = {'op': 'update', 'value': success}
            await self.send(reply, writer)

    async def send(self, msg, writer):
        ''' Sends a message asynchronously to the client. '''
        # print(datetime.datetime.now().isoformat(), '%s:'%self.name, 'Sending:', msg)
        msg['timestamp'] = datetime.datetime.now().isoformat()
        try:
            resp = dump(msg)
        except Exception as e:
            log.warn('Could not pickle message.')
            resp = dump({'op': 'update', 'value': 0})
        # import sys
        # print('SIZE:', sys.getsizeof(resp))
        writer.write(resp)

    async def handle_command(self, reader, writer):
        ''' Intercepts and reacts to a message from the client. '''
        while True:
            data = await reader.read(self.read_size)
            try:
                # message = json.loads(data.decode())
                message = load(data)
            except json.decoder.JSONDecodeError:
                print('JSON decode error')
                return
            # print(datetime.datetime.now().isoformat(), '%s:'%self.name, 'Received message:', message)
            op = message['op']
            if 'params' not in message:
                message['params'] = {}
            if op == 'connect':
                log.info('New listener at %s on port %i.', self.addr, self.port)
                await self.send({'op': 'update', 'params': 1}, writer)
                ''' Attempt to make reciprocal connection '''
                if not hasattr(self.node, 'sender'):
                    addr = message['params']['addr']
                    port = message['params']['port']
                    self.node.bind(addr, port)

            if op == 'check':
                active = self.node.api.check(message['params'])
                reply = {'op': 'update', 'value': active}
                await self.send(reply, writer)

            if op == 'echo':
                await self.send({'op': 'echo', 'params': message['params']}, writer)

            if op == 'event':
                self.node.api.event(message['params'])
                await self.confirm(writer)

            if op == 'get':
                value = self.node.api.get(message['target'], params=message['params'])
                await self.send({'op': op, 'value': value}, writer)

            if op == 'goto':
                ''' 'params' should contain a 'hub' to grab the sequencer from 
                     and a 'step' key that we want to go to '''
                self.node.api.goto(params=message['params'])
                await self.confirm(writer)

            if op == 'option':
                try:
                    self.node.api.option(message['params'])
                except Exception:
                    pass
                await self.confirm(writer)

            if op == 'plot':
                plot = self.node.api.plot(message['params'])
                reply = {'op': 'update',
                         'value': plot}
                await self.send(reply, writer)

            if op == 'set':
                self.node.api.set(message['target'], message['value'], message['params'])
                reply = {'op': 'set',
                         'target': message['target'],
                         'value': self.node.api.get(message['target'], params=message['params'])}
                await self.send(reply, writer)

            if op == 'shutdown':
                self.node.api.shutdown()
                await self.confirm(writer)
                self.node.close()
                import sys
                sys.exit()

            if op == 'run':
                self.node.api.run(message['params'])
                await self.confirm(writer)

            if op == 'terminate':
                self.node.api.terminate(message['params'])
                await self.confirm(writer)


class P2PNode():
    def __init__(self, name=None, addr = 'localhost', port = 29170, api = None):
        ''' Sets up a Listener on the passed address and port. '''
        self.api = api
        self.name=name
        self.listener = Listener(self, name, addr, port)
        self._connected = 0

    def bind(self, addr = 'localhost', port = 29171):
        self.sender = Sender(self, self.name, addr, port)
        self._connected = self.sender._hold_connection()

    def close(self):
        loops = [self.listener.loop]
        if hasattr(self, 'sender'):
            loops.append(self.sender.loop)
        for loop in loops:
            loop.call_soon_threadsafe(loop.stop)
            while loop.is_running():
                continue
            loop.close()

    def get(self, target, params = {}):
        return self.send({'op': 'get', 'target': target, 'params': params})['value']

    def send(self, message):
        if hasattr(self, 'sender'):
            return self.sender.send(message)

    def set(self, target, value, params = {}):
        if not hasattr(self, 'sender'):
            return
        self.send({'op': 'set', 'target': target, 'value': value, 'params': params})
        return self.get(target, params = params)


if __name__ == '__main__':
    log.basicConfig(level=log.INFO)

    n0 = P2PNode('master', 'localhost', 29170)
    n1 = P2PNode('dashboard', 'localhost', 29171)

    n0.bind('localhost', 29171)
