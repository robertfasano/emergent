from emergent.networks.Yb1.hubs.PA import Photoassociation
from emergent.networks.Yb1.devices.e4430b import E4430B
from emergent.devices.labjack import LabJack
from emergent.networks.monitor import network as monitor
from __main__ import *

def initialize(core):
    pa = Photoassociation(name = 'photoassociation', core = core, addr='127.0.0.1')
    pa.labjack = LabJack(name = 'labjack', params = {'devid': '440010742'}, parent = pa)
    pa.labjack.add_knob('TDAC6')

    synth = E4430B('synthesizer', parent = pa)

    # params = {'daqs': [{'name': 'labjack', 'params':{'devid': '440010742'}}],
    #           'watchdogs': {
    #                     'Lattice intensity': {'threshold': 0.1, 'channel': 'A0'},
    #                     'Lattice cavity': {'threshold': 0.1, 'channel': 'A1'},
    #                     'Blue Yb1 fiber': {'threshold': 3, 'channel': 'A2'},
    #                     'Blue error signal': {'threshold': 0.1, 'channel': 'A3'},
    #                     }
    #                  }
    # monitor.initialize(core, params = params)

    for hub in [pa]:
        core.add_hub(hub)
