from emergent.networks.Yb1.controls.lattice import Lattice
from emergent.networks.Yb1.controls.waveform import Ramp

from emergent.devices.labjack import LabJack

from __main__ import *

''' Define Lattice '''
lattice = Lattice(name='lattice', path='networks/%s'%sys.argv[1])
lattice.ljIN = LabJack(devid='470016973', name='labjack')
lattice.ljIN.prepare_streamburst(channel=0, trigger = 0, max_samples = lattice.max_samples)

lattice.ljOUT = LabJack(devid='470016970', name='labjack')

ramp = Ramp('ramp', .03, lattice.ljOUT, type={0:'linear', 1:'linear'}, steps=100, parent=lattice, trigger = 0)
