from __main__ import *
import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-3]))
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication
from emergent.gui.elements import MainFrame
from emergent.modules import Hub
from emergent.modules.server import Server
from emergent.modules.network import Network
import numpy as np
sys.path.append('networks/%s'%sys.argv[1])
import logging as log
import argparse
import importlib
import time



try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('EMERGENT')
except:
    pass
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

''' Create network object '''
network = Network()

''' Initialize network nodes '''
network_path = 'emergent.networks.%s'%sys.argv[1]
network_module = importlib.import_module('emergent.networks.%s'%sys.argv[1]+'.network')
if "__all__" in network_module.__dict__:
    names = network_module.__dict__["__all__"]
else:
    names = [x for x in network_module.__dict__ if not x.startswith("_")]
network_module.initialize(network)
network.load()

''' Run post-load routine '''
for c in Hub.instances:
    c.onLoad()

''' Do stuff '''
process = importlib.import_module('emergent.networks.%s'%sys.argv[1]+'.process')
if "__all__" in process.__dict__:
    names = process.__dict__["__all__"]
else:
    names = [x for x in process.__dict__ if not x.startswith("_")]
globals().update({k: getattr(process, k) for k in names})


if __name__ == "__main__":
    app = QCoreApplication.instance()
    if app is None:
        app = QApplication(sys.argv)         # Create an instance of the application

    main = MainFrame(app, network)
    main.show()
    app.processEvents()

    server = Server()
