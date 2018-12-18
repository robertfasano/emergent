
from __main__ import *
import sys
sys.path.append('/Users/rjf2/Documents/Projects/Ultraportable/portable/MOT theory')
sys.path.insert(0, 'C:\\Users\\Robbie\\Documents\\GitHub\\portable\\MOT theory')
from parameters import *
from thing import MOTHub, VirtualThing
gmot = MOTHub('gmot', path='networks/%s'%sys.argv[1])

coil1 = VirtualThing('coil1', gmot, inputs = ['R', 'z', 'N', 'I'])
coil2 = VirtualThing('coil2', gmot, inputs = ['R', 'z', 'N', 'I'])
grating = VirtualThing('grating', gmot, inputs = ['R1', 'd', 'position'])
trapping = VirtualThing('trapping', gmot, inputs = ['power', 'radius', 'detuning', 'polarization'])
slowing = VirtualThing('slowing', gmot, inputs = ['power', 'radius', 'detuning', 'polarization'])

gmot.actuate(state)
