
from __main__ import *
import sys
sys.path.append('/Users/rjf2/Documents/Projects/Ultraportable/portable/MOT theory')
sys.path.insert(0, 'C:\\Users\\Robbie\\Documents\\GitHub\\portable\\MOT theory')
from parameters import *
from device import MOTControl, CoilDevice, BeamDevice, GratingDevice



gmot = MOTControl('gmot', path='networks/%s'%sys.argv[1])
coil1 = CoilDevice('coil1', gmot)
coil2 = CoilDevice('coil2', gmot)
grating = GratingDevice('grating', gmot)
trapping = BeamDevice('trapping', gmot)
slowing = BeamDevice('slowing', gmot)

gmot.actuate(state)
