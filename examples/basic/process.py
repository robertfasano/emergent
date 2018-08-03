from __main__ import *

deviceA.inputs['X'].sequence = [(0,0), (0.5, 1)]
deviceA.inputs['Y'].sequence = [(0,0), (0.25,-1), (0.5,0), (0.75, 1)]
control.clock.add_input(deviceA.inputs['X'])
control.clock.add_input(deviceA.inputs['Y'])
#control.clock.start(3)
