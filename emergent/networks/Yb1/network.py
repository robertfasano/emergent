from emergent.networks.Yb1.controls.lattice import Lattice
from emergent.devices.labjackT7 import LabJack

from __main__ import *

''' Define Lattice '''
lattice = Lattice(name='lattice', path='networks/%s'%sys.argv[1])
labjack = LabJack(devid='470016973', name='labjack', parent = lattice)
lattice.add_labjack(labjack)
