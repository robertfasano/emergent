from emergent.networks.Yb1.hubs.lattice import Lattice
from emergent.networks.Yb1.hubs.waveform import Ramp
from emergent.modules import Thing
from emergent.things.labjack import LabJack

from __main__ import *

# ''' Define Lattice '''
# lattice = Lattice(name='lattice', path='networks/%s'%sys.argv[1])
# lattice.ljIN = LabJack(devid='470016973', name='labjack')
# lattice.ljIN.prepare_streamburst(channel=0, trigger = 0, max_samples = lattice.max_samples)
#
# lattice.ljOUT = LabJack(devid='470016970', name='labjack')


def initialize(network):
    lattice = Lattice('lattice', network = network)

    for hub in [monitor]:
        network.addHub(lattice)
