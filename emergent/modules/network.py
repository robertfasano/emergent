''' This module implements a container for multiple Hubs on a PC, as well as methods
    for getting or changing the state of Hubs on remote PCs.

    At runtime, main.py passes the Network object class into the EMERGENT network's
    initialize() method. For each local hub (Hub.addr matching the local address or
    unspecified), the Network adds the hub to its hubs dict. For each remote hub,
    the Network creates a Client. The Network.server object from server.py implements
    communications between nonlocal networks.
'''
import pickle
from emergent.utilities.networking import get_address
from emergent.utilities.testing import Timer
import importlib
from emergent.modules import Client, ProcessHandler
from emergent.protocols.tick import TICKClient
import time
from PyQt5.QtCore import QTimer
import logging as log

class Network():
    def __init__(self, name, addr = None, port = 9001, database_addr = None):
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
        self.path='networks/%s'%name
        self.data_path = self.path+'/data/'
        self.state_path = self.path+'/state/'
        self.params_path = self.path+'/params/'
        self.tree = None
        self.sync_delay = 0.1
        self.reconnect_delay = 1
        self.clients = {}
        self.hubs = {}
        self.params = {}
        self.manager = ProcessHandler()

    def __getstate__(self):
        ''' This method is called by the pickle module when attempting to serialize an
            instance of this class. We make sure to exclude any unpicklable objects from
            the return value, including anything with threads or Qt modules. '''
        d = {}
        ignore = ['manager', 'tree', 'update_timer']
        unpickled = []
        for item in ignore:
            if hasattr(self, item):
                unpickled.append(getattr(self,item))
        for item in self.__dict__:
            if self.__dict__[item] not in unpickled:
                d[item] = self.__dict__[item]
        return d

    def actuate(self, state):
        ''' Issues a macroscopic actuation to all connected Hubs. '''
        for hub in state:
            self.hubs[hub].actuate(state[hub])

    def addHub(self, hub):
        ''' If the address and port match self.addr and self.port, add a local hub. Otherwise,
            check if they match any in self.clients and assign to that one; otherwise, create a new client. '''
        if hub.addr is not None:
            if not hub.addr == self.addr:
                if hub.addr not in self.clients:
                    self.clients[hub.addr] = Client(hub.addr, self.port)
                return

        self.hubs[hub.name] = hub
        hub.network = self

    def add_params(self, params):
        for hub in params:
            if hub not in self.params:
                self.params[hub] = {}
            for thing in params[hub]:
                self.params[hub][thing] = params[hub][thing]

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
            hub.onLoad()

    def save(self):
        ''' Saves the state of all attached Hubs. '''
        for hub in self.hubs.values():
            hub.save()

    def state(self):
        ''' Obtains a macroscopic state dict from aggregating the states of all
            attached Hubs. '''
        state = {}
        for hub in self.hubs.values():
            state[hub.name] = hub.state

        return state

    def keep_sync(self):
        ''' Queries the state of all remote networks at a rate given by self.sync_delay. '''
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.sync)
        self.update_timer.start(self.sync_delay*1000)

    def try_connect(self):
        ''' Continuously attempts to connect to any not-yet-connected clients at a rate
            given by self.reconnect_delay. Returns once all clients are connected. '''
        while True:
            disconnected_clients = len(self.clients)
            for client in self.clients.values():
                if not client._connected:
                    try:
                        client.connect()
                    except ConnectionRefusedError: #note: using localhost instead of 127.0.0.1 will throw multiple exceptions here
                        continue
                else:
                    disconnected_clients -= 1
            if disconnected_clients == 0:
                return
            time.sleep(self.reconnect_delay)

    def save_to_database(self):
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
                log.warn('Connection refused by server at %s:%i.'%(client.addr, client.port))
            self.tree.generate(client.network)
