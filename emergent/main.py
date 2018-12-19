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
import time
import importlib

''' Register app with OS '''
try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('EMERGENT')
except:
    pass

''' Parse arguments and set verbosity for logging '''
parser = argparse.ArgumentParser()
parser.add_argument("name", help="Network name")
parser.add_argument("--addr", help='EMERGENT session IP address')
parser.add_argument("--port", help='EMERGENT session networking port')
parser.add_argument("-v", "--verbose", help="Increase output verbosity", action="store_true")
args = parser.parse_args()
if args.verbose:
    log.basicConfig(level=log.DEBUG)
else:
    log.basicConfig(level=log.INFO)

''' Initialize network  '''
addr = None
if args.addr:
    addr = args.addr
port = None
if args.port:
    port = args.port
network = Network(name=args.name, addr = addr, port = port)
network.initialize()        # instantiate nodes
network.load()              # load previous state from file
network.post_load()         # run post-load routine to prepare physical state

''' Do stuff defined in the network's process.py file '''
process = importlib.import_module('emergent.networks.'+network.name+'.process')
if "__all__" in process.__dict__:
    names = process.__dict__["__all__"]
else:
    names = [x for x in process.__dict__ if not x.startswith("_")]
globals().update({k: getattr(process, k) for k in names})

if __name__ == "__main__":
    # app = QCoreApplication.instance()
    app = None
    if app is None:
        app = QApplication(sys.argv)         # Create an instance of the application

    main = MainFrame(app, network)
    network.keep_sync()     # sync network with all other EMERGENT sessions

    main.show()
    app.processEvents()

    server = Server(network)
