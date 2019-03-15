''' This module launches an EMERGENT session.

    Args:
        name: the name of a network in the emergent/networks folder
        --addr: specify an IP address if you want to define localhost for testing
        --port: the networking port of a decentralized EMERGENT session
        --database_addr: the IP address of a remote InfluxDB server
        --verbose: increase the output verbosity for debugging
'''
#from __main__ import *
import sys
import os
import logging as log
import argparse
import importlib
from PyQt5.QtWidgets import QApplication, QStyleFactory
from emergent.dashboard.gui import Dashboard
from emergent.utilities.networking import get_address

''' Register app with OS '''
try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('EMERGENT Dashboard')
except AttributeError:
    pass


''' Parse arguments and set verbosity for logging '''
parser = argparse.ArgumentParser()
parser.add_argument("--addr", help='EMERGENT session IP address')
parser.add_argument("--port", help='EMERGENT session port')
parser.add_argument("-v", "--verbose", help="Increase output verbosity", action="store_true")
args = parser.parse_args()
if args.verbose:
    log.basicConfig(level=log.DEBUG)
else:
    log.basicConfig(level=log.INFO)
if args.addr:
    addr = args.addr
else:
    # addr = 'localhost'
    addr = get_address()
if args.port:
    port = args.port
else:
    port = 5000

def launch():
    run_frontend()



def run_frontend():
    QApplication.setStyle(QStyleFactory.create("Fusion"))
    app = QApplication.instance()
    if app is None:
        app = QApplication([" "])         # Create an instance of the application
    app.setStyle(QStyleFactory.create("Fusion"))
    global dash
    dash = Dashboard(app, addr, port)
    dash.show()
    app.processEvents()
    app.exec()

if __name__ == '__main__':
    launch()
