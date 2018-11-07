
from __main__ import *
import sys
sys.path.append('/Users/rjf2/Documents/Projects/Ultraportable/portable/MOT theory')
sys.path.insert(0, 'C:\\Users\\Robbie\\Documents\\GitHub\\portable\\MOT theory')
from parameters import *
from device import MOTControl, VirtualDevice
gmot = MOTControl('gmot', path='networks/%s'%sys.argv[1])

coil1 = VirtualDevice('coil1', gmot, inputs = ['R', 'z', 'N', 'I'])
coil2 = VirtualDevice('coil2', gmot, inputs = ['R', 'z', 'N', 'I'])
grating = VirtualDevice('grating', gmot, inputs = ['R1', 'd', 'position'])
trapping = VirtualDevice('trapping', gmot, inputs = ['power', 'radius', 'detuning', 'polarization'])
slowing = VirtualDevice('slowing', gmot, inputs = ['power', 'radius', 'detuning', 'polarization'])

gmot.actuate(state)
