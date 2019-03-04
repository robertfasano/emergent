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

class Network():
    ''' This class implements a container for multiple Hubs on a PC, as well as methods
        for getting or changing the state of Hubs on remote PCs.

        At runtime, main.py passes the Network object class into the EMERGENT network's
        initialize() method. For each local hub (Hub.addr matching the local address or
        unspecified), the Network adds the hub to its hubs dict. For each remote hub,
        the Network creates a Client. The Network.server object from server.py implements
        communications between nonlocal networks.
    '''
    def __init__(self, name, addr=None, port=9001, database_addr=None):
        self.addr = addr
        if self.addr is None:
            self.addr = get_address()
        if database_addr is not None:
            self.database = TICKClient(database_addr, 'admin', 'admin', name)
            already_exists = False
            dbs = self.database.client.get_list_database()
            for db in dbs:
                if db['name'] == name:
                    already_exists = True
                    break
            if not already_exists:
                self.database.client.create_database(name)
        self.port = port
        self.timer = Timer()
        self.name = name
        self.path = {'network': 'networks/%s'%name}
        self.path['data'] = self.path['network']+'/data/'
        self.path['state'] = self.path['network']+'/state/'
        self.path['params'] = self.path['network']+'/params/'
        self.tree = None
        self.connection_params = {'sync delay': 0.1, 'reconnect delay': 1}
        self.clients = {}
        self.hubs = {}
        self.params = {}
        self.manager = ProcessHandler()
        self.update_timer = QTimer()

    def __getstate__(self):
        ''' This method is called by the pickle module when attempting to serialize an
            instance of this class. We make sure to exclude any unpicklable objects from
            the return value, including anything with threads or Qt modules. '''
        d = {}
        ignore = ['manager', 'tree', 'update_timer']
        unpickled = []
        for item in ignore:
            if hasattr(self, item):
                unpickled.append(getattr(self, item))
        for item in self.__dict__:
            if self.__dict__[item] not in unpickled:
                d[item] = self.__dict__[item]
        return d

    def actuate(self, state, send_over_p2p = True):
        ''' Issues a macroscopic actuation to all connected Hubs. '''
        for hub in state:
            self.hubs[hub].actuate(state[hub], send_over_p2p)

    def add_hub(self, hub):
        ''' If the address and port match self.addr and self.port, add a local
            hub. Otherwise, check if they match any in self.clients and assign
            to that one; otherwise, create a new client. '''
        if hub.addr is not None:
            if not hub.addr == self.addr:
                if hub.addr not in self.clients:
                    self.clients[hub.addr] = Client(hub.addr, self.port)
                return

        self.hubs[hub.name] = hub
        hub.network = self

    def add_params(self, params):
        ''' Add parameters passed in from the network's initialize() method
            to allow custom chunked networks to be constructed. '''
        for hub in params:
            if hub not in self.params:
                self.params[hub] = {}
            for thing in params[hub]:
                self.params[hub][thing] = params[hub][thing]

    def add_thing(self):
        self.thing_creator = ThingCreator(self)
        self.thing_creator.show()

    def initialize(self):
        ''' Import the network.py file for the user-specified network and runs
            its initialize() method to instantiate all defined nodes. '''
        network_module = importlib.import_module('emergent.networks.'+self.name+'.network')
        network_module.initialize(self)

    def load(self):
        ''' Loads all attached Hub states from file. '''
        for hub in self.hubs.values():
            hub.load()

    def post_load(self):
        ''' Execute the post-load routine for all attached Hubs '''
        for hub in self.hubs.values():
            hub.on_load()

    def save(self):
        ''' Saves the state of all attached Hubs. '''
        for hub in self.hubs.values():
            hub.save()

    def set_settings(self, settings):
        for hub_name in settings:
            hub = self.hubs[hub_name]
            for thing_name in settings[hub_name]:
                for input_name in settings[hub_name][thing_name]:
                    d = settings[hub_name][thing_name][input_name]
                    for qty in ['min', 'max']:
                        if qty in d:
                            hub.settings[thing_name][input_name][qty] = d[qty]

    def settings(self):
        ''' Obtains a macroscopic settings dict from aggregating the settings of all
            attached Hubs. '''
        settings = {}
        for hub in self.hubs.values():
            settings[hub.name] = hub.settings

        return settings

    def state(self):
        ''' Obtains a macroscopic state dict from aggregating the states of all
            attached Hubs. '''
        state = {}
        for hub in self.hubs.values():
            state[hub.name] = hub.state

        return state

    def keep_sync(self):
        ''' Queries the state of all remote networks at a rate given by
            self.connection_params['sync delay']. '''
        self.update_timer.timeout.connect(self.sync)
        self.update_timer.start(self.connection_params['sync delay']*1000)

    def try_connect(self):
        ''' Continuously attempts to connect to any not-yet-connected clients at
            a rate given by self.connection_params['reconnect delay']. Returns
            once all clients are connected. '''
        while True:
            disconnected_clients = len(self.clients)
            for client in self.clients.values():
                if not client._connected:
                    try:
                        client.connect()
                    except ConnectionRefusedError:
                        ''' note: using localhost instead of 127.0.0.1 will throw
                            multiple exceptions here '''
                        continue
                else:
                    disconnected_clients -= 1
            if disconnected_clients == 0:
                return
            time.sleep(self.connection_params['reconnect delay'])

    def save_to_database(self):
        ''' Write the network state to the database. '''
        if hasattr(self, 'database'):
            self.database.write_network_state(self.state())

    def sync(self):
        ''' Queries each connected client for the state of its Network, then updates
            the NetworkPanel to show the current state of the entire network. '''
        for client in self.clients.values():
            if not client._connected:
                continue
            try:
                client.network = client.get_network()
            except ConnectionRefusedError:
                self.update_timer.stop()
                log.warning('Connection refused by server at %s:%i.', client.addr, client.port)
            self.tree.generate(client.network)
