''' This script launches the EMERGENT dashboard.

    Args:
        name: the name of a network in the emergent/networks folder
        --addr: address of the master API
        --port: port of the master API
'''
import os
import logging as log
import argparse
from PyQt5.QtWidgets import QApplication, QStyleFactory
from emergent.dashboard.gui import Dashboard

''' Register app with OS '''
if os.name == 'nt':
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('EMERGENT Dashboard')

''' Parse arguments and set verbosity for logging '''
parser = argparse.ArgumentParser()
parser.add_argument("--addr", help='EMERGENT session IP address', default='127.0.0.1')
parser.add_argument("--port", help='EMERGENT session port', default=5000, type=int)
args = parser.parse_args()


QApplication.setStyle(QStyleFactory.create("Fusion"))
app = QApplication.instance()
if app is None:
    app = QApplication([" "])         # Create an instance of the application
app.setStyle(QStyleFactory.create("Fusion"))
global dash
dash = Dashboard(app, args.addr, args.port)
dash.show()
