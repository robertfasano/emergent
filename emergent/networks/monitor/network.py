from emergent.networks.monitor.hubs.monitor import Monitor
from emergent.things.labjack import LabJack
from emergent.modules import Watchdog

from __main__ import *

def initialize(network):
    monitor = Monitor('monitor', network = network)
    monitor.labjack = LabJack(devid='440010742', name='labjack', parent = monitor)
    monitor.watchdogs['CH0'] = Watchdog(parent = monitor, experiment = monitor.measure_CH0, name = 'CH0', threshold = 0.5)
    monitor.watchdogs['CH1'] = Watchdog(parent = monitor, experiment = monitor.measure_CH1, name = 'CH1', threshold = 1)

    for hub in [monitor]:
        network.addHub(hub)
