from __main__ import *

deviceA.children['X'].sequence = [(0,0), (0.5, 1)]
deviceA.children['Y'].sequence = [(0,0), (0.25,-1), (0.5,0), (0.75, 1)]
control.clock.add_input(deviceA.children['X'])
control.clock.add_input(deviceA.children['Y'])
#control.clock.start(3)
