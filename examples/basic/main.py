import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-3]))
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication
from emergent.gui.elements.treeview import MainFrame
from emergent.archetypes.node import Control

import numpy as np

''' Import network '''
from network import *

''' Do stuff '''
from process import *

''' Gather nodes '''
tree = {}
controls = Control.instances
for control in controls:
    tree[control.name] = {}
    for device in control.devices.values():
        tree[control.name][device.name] = []
        for input in device.inputs.values():
            tree[control.name][device.name].append(input.name)

if __name__ == "__main__":
    app = QCoreApplication.instance()
    if app is None:
        app = QApplication(sys.argv)         # Create an instance of the application

    main = MainFrame(tree, control)
    main.show()
