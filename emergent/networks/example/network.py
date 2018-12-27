from emergent.networks.example.hubs.testHub import TestHub
from emergent.networks.example.things.testThing import TestThing
from emergent.networks.example.watchdogs.testWatchdog import TestWatchdog
import sys
import socket

def initialize(network, params = {}):
    network.add_params(params)          # add the passed params to the network

    autoAlign = TestHub('autoAlign', network = network)
    autoAlign.watchdogs['watchdog'] = TestWatchdog(autoAlign, experiment = autoAlign.transmitted_power, name = 'fiber power')

    MEMS = TestThing('MEMS', params = {'inputs': ['X', 'Y']}, parent=autoAlign)
    otherHub = TestHub('otherHub', addr = '127.0.0.1', network = network)
    otherThing = TestThing('otherThing', params = {'inputs': ['Z']}, parent=otherHub)

    ''' Add hubs to network '''
    for hub in [autoAlign, otherHub]:
        network.addHub(hub)
