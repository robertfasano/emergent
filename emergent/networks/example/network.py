from emergent.networks.example.hubs.testHub import TestHub
from emergent.networks.example.things.testThing import TestThing
import sys
import socket
#
def initialize(network):
    addr = socket.gethostbyname(socket.gethostname())
    autoAlign = TestHub('autoAlign', addr = '192.168.0.107')
    MEMS = TestThing('MEMS', parent=autoAlign, inputs = ['X', 'Y'])
    otherHub = TestHub('otherHub', addr = '192.168.0.108')
    otherThing = TestThing('otherThing', parent=otherHub, inputs = ['X', 'Y'])

    network.addHub(autoAlign)
