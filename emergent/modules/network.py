import sys
import os
import pickle
import pathlib
from emergent.utility import Timer, get_address
import importlib
from emergent.modules.client import Client
import time
from PyQt5.QtCore import QTimer
import logging as log
from emergent.modules import ProcessHandler

class Network():
    def __init__(self, name, addr = None, port = 9001):
        self.addr = addr
        if self.addr is None:
            self.addr = get_address()
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
        for p in [self.state_path, self.data_path, self.params_path]:
            pathlib.Path(p).mkdir(parents=True, exist_ok=True)
        self.clients = {}
        self.hubs = {}
        self.manager = ProcessHandler()

    def __getstate__(self):
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

    # def connect_remotes(self):
    #     for c in self.clients:
    #         client = self.clients[c]
    #         client._run_thread(client.connect)

    def initialize(self):
        network_module = importlib.import_module('emergent.networks.'+self.name+'.network')
        network_module.initialize(self)

    def load(self):
        for hub in self.hubs.values():
            hub.load()

    def post_load(self):
        for hub in self.hubs.values():
            hub.onLoad()

    def save(self):
        for hub in self.hubs.values():
            hub.save()

    def state(self):
        state = {}
        for hub in self.hubs.values():
            state[hub.name] = hub.state

        return state

    def keep_sync(self):
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.sync)
        self.update_timer.start(self.sync_delay*1000)

    def try_connect(self):
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

    def sync(self):
        ''' Updates the local session with remote networks '''
        for client in self.clients.values():
            if not client._connected:
                continue
            try:
                client.network = client.get_network()
            except ConnectionRefusedError:
                self.update_timer.stop()
                log.warn('Connection refused by server at %s:%i.'%(client.addr, client.port))
            self.tree.generate(client.network)
