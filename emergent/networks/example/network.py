from emergent.networks.example.hubs.testHub import TestHub
from emergent.networks.example.things.testThing import TestThing
import sys

autoAlign = TestHub('autoAlign', path='networks/%s'%sys.argv[1])
MEMS = TestThing('MEMS', parent=autoAlign, inputs = ['X', 'Y'])
