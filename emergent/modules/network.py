import sys
import os
import pickle
import pathlib
from emergent.utility import Timer
import importlib

class Network():
    def __init__(self, name):
        self.timer = Timer()
        self.name = name
        self.path='networks/%s'%name
        self.data_path = self.path+'/data/'
        self.state_path = self.path+'/state/'

        for p in [self.state_path, self.data_path]:
            pathlib.Path(p).mkdir(parents=True, exist_ok=True)

        self.hubs = {}

    def actuate(self, state):
        for hub in state:
            self.hubs[hub].actuate(state[hub])
            
    def addHub(self, hub):
        self.hubs[hub.name] = hub
        hub.network = self

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
