''' This module handles communications between EMERGENT sessions on remote
    networked PCs through a symmetric client/server protocol. '''

import asyncio
import json
import time
from threading import Thread
import logging as log
import pickle
import importlib
from PyQt5.QtCore import QTimer
from emergent.utilities.networking import get_address
from emergent.utilities.testing import Timer
from emergent.modules import ProcessHandler
from emergent.protocols.tick import TICKClient
from emergent.gui.elements import ThingCreator
import cherrypy

class Client():
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
    def __init__(self, addr, port=8888):
        self.addr = addr
        self.port = port
        self._connected = False

    def __getstate__(self):
        ''' Returns a dictionary for byte serialization when requested by the
            pickle module. '''
        d = {}
        ignore = ['network']
        unpickled = []
        for item in ignore:
            if hasattr(self, item):
                unpickled.append(getattr(self, item))
        for item in self.__dict__:
            if self.__dict__[item] not in unpickled:
                d[item] = self.__dict__[item]
        return d

    def actuate(self, state):
        ''' Sends a command to the server to actuate remote inputs. '''
        return asyncio.run(self.send({'op': 'actuate', 'params': state}))[0]

    def connect(self):
        ''' Initialize a connection with the server. '''
        self._connected = asyncio.run(self.send({'op': 'connect'}))[0]['params']

    def echo(self, message):
        ''' Client/server echo for debugging '''
        message = {'op': 'echo', 'params': message}
        resp = self.send(message)
        return resp

    async def send(self, message):
        ''' Passes a message to the server asynchronously and returns the response. '''
        loop = asyncio.get_event_loop()
        response = await asyncio.gather(self.tcp_echo_client(message, loop))
        return response

    async def tcp_echo_client(self, message, loop):
        ''' Passes a message to the server. '''
        reader, writer = await asyncio.open_connection(self.addr, self.port,
                                                       loop=loop)
        writer.write(json.dumps(message).encode())
        await writer.drain()
        data = await reader.read()
        writer.close()
        return pickle.loads(data)

    def get_network(self):
        ''' Queries the server for the remote network. '''
        return asyncio.run(self.send({'op': 'get_network'}))[0]

    def get_state(self):
        ''' Queries the server for the remote network state. '''
        network = asyncio.run(self.send({'op': 'get_network'}))[0]
        return network.state()

    def get_settings(self, hub):
        ''' Queries the server for the remote network state. '''
        network = asyncio.run(self.send({'op': 'get_network'}))[0]
        return network.hubs[hub].settings

    def get_params(self):
        ''' Queries the server for connection parameters. '''
        return asyncio.run(self.send({'op': 'get_params'}))[0]

    def set_range(self, d):
        return asyncio.run(self.send({'op': 'set_range', 'params': d}))[0]

class Server():
    ''' The Server class, along with the Client class in client.py, handles communication
        between remote EMERGENT sessions. When the EMERGENT network is initialized, all
        PCs in the session create a server to handle the following client commands:

        * _connect(): attempts to contact the server and sets self._connected=True if successful
        * actuate(state): tells the target server to call its local cluster's actuate() method
        * echo(msg): sends a command to the server and nominally receives the command back
        * get_network(): requests the current state of a remote cluster
        * get_params(): requests operational parameters from the server
    '''

    def __init__(self, addr = None, port = None):
        ''' Sets up a new thread for serving. '''
        self.params = {'tick': 500}
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        self.addr = addr
        if self.addr is None:
            self.addr = '127.0.0.1'
        self.port = port
        if self.port is None:
            self.port = 29170

        coro = asyncio.start_server(self.handle_command, self.addr, self.port, loop=self.loop)
        if not self.loop.is_running():
            self.server = self.loop.run_until_complete(coro)
        else:
            asyncio.ensure_future(coro, loop=self.loop)
        thread = Thread(target=self.start)
        thread.start()

    async def actuate(self, state, writer):
        ''' Actuates local inputs in response to a remote request and confirms
            success with the client. '''
        self.network.actuate(state)
        await self.send({'op': 'update', 'params': 1}, writer)

    async def set_range(self, state, writer):
        ''' Actuates local inputs in response to a remote request and confirms
            success with the client. '''
        hub = list(state.keys())[0]
        thing = list(state[hub].keys())[0]
        input = list(state[hub][thing].keys())[0]
        d = state[hub][thing][input]
        self.network.hubs[hub].settings[thing][input] = d
        print(self.network.hubs[hub].settings)
        await self.send({'op': 'update', 'params': 1}, writer)

    async def echo(self, message, writer):
        ''' Client/server echo for debugging '''
        await self.send(message, writer)

    def start(self):
        ''' Start the server. '''
        if not self.loop.is_running():
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
        op = message['op']

        if 'get' in op:
            var = getattr(self, op.split('_')[1])
            await self.send(var, writer)
        elif op == 'connect':
            await self.add_listener(writer)
        elif op == 'actuate':
            await self.actuate(message['params'], writer)
        elif op == 'echo':
            await self.echo(message['params'], writer)
        elif op == 'set_range':
            await self.set_range(message['params'], writer)


    async def add_listener(self, writer):
        ''' Confirm a new connection to a client. '''
        log.info('New listener at %s on port %i.', self.addr, self.port)
        await self.send({'op': 'update', 'params': 1}, writer)
