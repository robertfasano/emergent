from emergent.networks.example.controls.testControl import TestControl
from emergent.networks.example.devices.testDevice import TestDevice
import sys

autoAlign = TestControl('autoAlign', path='networks/%s'%sys.argv[1])
MEMS = TestDevice('MEMS', parent=autoAlign, inputs = ['X', 'Y'])
