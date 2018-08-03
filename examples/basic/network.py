from emergent.controls.testControl import TestControl
from emergent.devices.testDevice import TestDevice

control = TestControl('control')
deviceA = TestDevice('deviceA', parent=control)
deviceB = TestDevice('deviceB', parent=control)
