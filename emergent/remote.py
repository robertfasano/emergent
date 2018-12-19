from __main__ import *
import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-3]))
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication
from emergent.gui.elements import RemoteViewer
from emergent.modules import Hub
import numpy as np
import logging as log
import argparse
import importlib
try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('EMERGENT remote')
except:
    pass


if __name__ == "__main__":
    app = QCoreApplication.instance()
    if app is None:
        app = QApplication(sys.argv)         # Create an instance of the application
    addr = sys.argv[1]
    main = RemoteViewer(app, addr)
    main.show()
    app.processEvents()
