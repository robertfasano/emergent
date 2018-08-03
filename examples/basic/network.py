from controls.testControl import TestControl
from devices.testDevice import TestDevice
import sys

control = TestControl('control', path='examples/%s'%sys.argv[1])
deviceA = TestDevice('deviceA', parent=control)
deviceB = TestDevice('deviceB', parent=control)
