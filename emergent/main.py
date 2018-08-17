from __main__ import *
import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-3]))
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication
from emergent.gui.elements.window import MainFrame
from emergent.archetypes.node import Control
import numpy as np
sys.path.append('networks/%s'%sys.argv[1])
import logging as log
import argparse
import importlib

parser = argparse.ArgumentParser()
parser.add_argument("path")
parser.add_argument("-v", "--verbose", help="Increase output verbosity", action="store_true")
parser.add_argument("-s", "--simulation", help="Start the network in simulation mode", action = "store_true")
args = parser.parse_args()
if args.verbose:
    log.basicConfig(level=log.DEBUG)
else:
    log.basicConfig(level=log.INFO)

if args.simulation:
    log.warn('Starting %s network in simulation mode.'%args.path)
else:
    log.info('Starting %s network.'%args.path)
global simulation
simulation = args.simulation

''' Import network '''
# from network import *
network = importlib.import_module('emergent.networks.%s'%sys.argv[1]+'.network')
if "__all__" in network.__dict__:
    names = network.__dict__["__all__"]
else:
    names = [x for x in network.__dict__ if not x.startswith("_")]
globals().update({k: getattr(network, k) for k in names})
''' Do stuff '''
process = importlib.import_module('emergent.networks.%s'%sys.argv[1]+'.process')
if "__all__" in process.__dict__:
    names = process.__dict__["__all__"]
else:
    names = [x for x in process.__dict__ if not x.startswith("_")]
globals().update({k: getattr(process, k) for k in names})

''' Gather nodes '''
tree = {}
controls = Control.instances
for control in controls:
    tree[control.name] = {}
    for device in control.children.values():
        tree[control.name][device.name] = []
        for input in device.children.values():
            tree[control.name][device.name].append(input.name)




controls_dict = {}
for c in controls:
    controls_dict[c.name] = c
if __name__ == "__main__":
    app = QCoreApplication.instance()
    if app is None:
        app = QApplication(sys.argv)         # Create an instance of the application

    main = MainFrame(app, tree, controls_dict)
    main.show()
