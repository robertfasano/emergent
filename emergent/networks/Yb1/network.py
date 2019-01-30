from emergent.networks.Yb1.hubs.PA import Photoassociation
from emergent.networks.Yb1.things.e4430b import E4430B
from emergent.things.labjack import LabJack
from emergent.networks.monitor import network as monitor
from __main__ import *

def initialize(network):
    pa = Photoassociation(name = 'photoassociation', network = network)
    pa.labjack = LabJack(name = 'labjack', params = {'devid': '440010742'}, parent = pa)
    pa.labjack.add_input('TDAC6')

    synth = E4430B('synthesizer', parent = pa)

    # params = {'daqs': [{'name': 'labjack', 'params':{'devid': '440010742'}}],
    #           'watchdogs': {
    #                     'Lattice intensity': {'threshold': 0.1, 'channel': 'A0'},
    #                     'Lattice cavity': {'threshold': 0.1, 'channel': 'A1'},
    #                     'Blue Yb1 fiber': {'threshold': 3, 'channel': 'A2'},
    #                     'Blue error signal': {'threshold': 0.1, 'channel': 'A3'},
    #                     }
    #                  }
    # monitor.initialize(network, params = params)

    for hub in [pa]:
        network.addHub(hub)
