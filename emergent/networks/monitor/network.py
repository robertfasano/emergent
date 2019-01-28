from emergent.networks.monitor.hubs.monitor import Monitor

from __main__ import *


def initialize(network, params = {}):
    if params == {}:
        params = {'daq': {'type': 'labjack', 'addr': '440010742'},
                  'watchdogs': {
                            'CH0': {'threshold': 0.5, 'channel': 0},
                            'CH1': {'threshold': 1, 'channel': 1},
                            }
                         }
    monitor = Monitor('monitor', network = network, params = params)


    for hub in [monitor]:
        network.addHub(hub)
