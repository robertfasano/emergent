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

log.basicConfig(level=log.INFO)

def launch():
    # client = Client(get_address(), 8000)
    # server = Server()


    from emergent.protocols.p2p import P2PNode
    global dashP2P
    dashP2P = P2PNode('dashboard', 'localhost', 27191)
    dashP2P.bind('localhost', 27190)
    while not dashP2P._connected:
        continue
    run_frontend(dashP2P)



def run_frontend(dashP2P):
    QApplication.setStyle(QStyleFactory.create("Fusion"))
    app = QApplication.instance()
    if app is None:
        app = QApplication([" "])         # Create an instance of the application
    app.setStyle(QStyleFactory.create("Fusion"))
    global dash
    dash = Dashboard(app, dashP2P)
    dash.show()
    app.processEvents()
    app.exec()

if __name__ == '__main__':
    launch()
