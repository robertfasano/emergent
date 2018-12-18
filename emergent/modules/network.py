import sys
import os
import pickle
import pathlib
from utility import Timer

class Network():
    def __init__(self):
        self.timer = Timer()
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
            hub.load_all()
