from emergent.networks.Yb1.controls.lattice import Lattice
from emergent.networks.Yb1.controls.waveform import LinearRamp

from emergent.devices.labjackT7 import LabJack

from __main__ import *

''' Define Lattice '''
lattice = Lattice(name='lattice', path='networks/%s'%sys.argv[1])
lattice.ljIN = LabJack(devid='470016973', name='labjack')
lattice.ljIN.prepare_streamburst(channel=0, trigger = 0, max_samples = lattice.max_samples)

lattice.ljOUT = LabJack(devid='470016970', name='labjack')
lattice.ljOUT.prepare_stream_out(['DAC0'], trigger = 0)

intensity_ramp = LinearRamp('intensity_ramp', .03, lattice.ljOUT, parent=lattice)
