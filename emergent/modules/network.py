import sys
import os
import pickle
import pathlib

class Network():
    def __init__(self):
        self.name = sys.argv[1]
        self.path='networks/%s'%sys.argv[1]
        self.data_path = self.path+'/data/'
        self.state_path = self.path+'/state/'

        for p in [self.state_path, self.data_path]:
            pathlib.Path(p).mkdir(parents=True, exist_ok=True)

        self.hubs = {}

    def addHub(self, hub):
        self.hubs[hub.name] = hub
        hub.network = self

    def load(self):
        for hub in self.hubs.values():
            for thing in hub.children.values():
                for input in thing.children.values():
                    hub.load(thing.name, input.name)
