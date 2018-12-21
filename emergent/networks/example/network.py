from emergent.networks.example.hubs.testHub import TestHub
from emergent.networks.example.things.testThing import TestThing
from emergent.networks.example.watchdogs.testWatchdog import TestWatchdog
import sys
import socket
#
def initialize(network):
    autoAlign = TestHub('autoAlign', network = network)
    autoAlign.watchdogs['watchdog'] = TestWatchdog(autoAlign, experiment = autoAlign.transmitted_power, name = 'fiber power')

    MEMS = TestThing('MEMS', parent=autoAlign, inputs = ['X', 'Y'])
    otherHub = TestHub('otherHub', addr = '127.0.0.1', network = network)
    otherThing = TestThing('otherThing', parent=otherHub, inputs = ['X', 'Y'])

    for hub in [autoAlign, otherHub]:
        network.addHub(hub)
