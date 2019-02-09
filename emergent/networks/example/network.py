from emergent.networks.example.hubs.testHub import TestHub
from emergent.networks.example.things.testThing import TestThing
from emergent.networks.example.watchdogs.testWatchdog import TestWatchdog
import sys
import socket

def initialize(network, params = {}):
    network.add_params(params)          # add the passed params to the network

    autoAlign = TestHub('autoAlign', network = network)
    autoAlign.watchdogs['watchdog'] = TestWatchdog(autoAlign, experiment = autoAlign.transmitted_power, name = 'fiber power')

    MEMS = TestThing('MEMS', params = {'inputs': ['X', 'Y']}, parent=autoAlign)
    otherHub = TestHub('otherHub', addr = '127.0.0.1', network = network)
    otherThing = TestThing('otherThing', params = {'inputs': ['Z']}, parent=otherHub)

    ''' Add switches '''
    from emergent.modules.switch import Switch
    autoAlign.switches['Switch A'] = Switch('Switch A', {}, invert = False)
    autoAlign.switches['Switch B'] = Switch('Switch B', {}, invert = False)

    ''' Add sequencing '''
    from emergent.modules.sequencing import Timestep, Sequencer
    A_ON = Timestep('A_ON', duration = 0.7, state = {'Switch A': 1, 'Switch B': 0})
    B_ON = Timestep('B_ON', duration = 0.3, state ={'Switch A': 0, 'Switch B': 1})

    sequencer = Sequencer('sequencer', parent = autoAlign, params = {'steps': [A_ON, B_ON], 'labjack': None})

    ''' Add hubs to network '''
    for hub in [autoAlign, otherHub]:
        network.add_hub(hub)
