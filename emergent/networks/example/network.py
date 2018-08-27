from emergent.networks.example.controls.testControl import TestControl
from emergent.networks.example.devices.testDevice import TestDevice
import sys

control = TestControl('control', path='networks/%s'%sys.argv[1])
deviceA = TestDevice('deviceA', parent=control)
deviceB = TestDevice('deviceB', parent=control)


control.onLoad()
