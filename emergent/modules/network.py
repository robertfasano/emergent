import sys
import os
import pickle
import pathlib
from emergent.utility import Timer, get_address
import importlib
from emergent.modules.client import Client

class Network():
    def __init__(self, name):
        self.timer = Timer()
        self.name = name
        self.path='networks/%s'%name
        self.data_path = self.path+'/data/'
        self.state_path = self.path+'/state/'
        self.tree = None

        for p in [self.state_path, self.data_path]:
            pathlib.Path(p).mkdir(parents=True, exist_ok=True)
        self.clients = {}
        self.hubs = {}

    def actuate(self, state):
        for hub in state:
            self.hubs[hub].actuate(state[hub])

    def addHub(self, hub):
        if not hub.local:
            ''' Attempt to connect over TCP/IP '''
            if hub.address is not None:
                if hub.address != get_address():
                    self.clients[hub.name] = Client(hub.address)
            return

        self.hubs[hub.name] = hub
        hub.network = self

    def connect_remotes(self):
        self.remotes = {}
        for c in self.clients:
            client = self.clients[c]
            client.connect()
            self.remotes[c] = client.get_network()
            
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
