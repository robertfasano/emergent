import sys
import os
import pickle

class Network():
    def __init__(self):
        self.name = sys.argv[1]
        self.path='networks/%s'%sys.argv[1]
        self.data_path = self.path+'/data/'
        self.hubs = {}
        
    def addHub(self, hub):
        self.hubs[hub.name] = hub
