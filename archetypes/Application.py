from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QCoreApplication
import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-1]))
from emergent.archetypes.node import Input, Device, Control

''' Create application and engine '''
app = QCoreApplication.instance()
if app is None:
    app = QApplication(sys.argv)
engine = QQmlApplicationEngine()

engine.load("gui/main.qml")                     # Load the qml file into the engine
window = engine.rootObjects()[0]
window.show()

''' Gather nodes '''
tree = {}
controls = Control.instances
for control in controls:
    tree[control.name] = {}
    for device in control.devices.values():
        tree[control.name][device.name] = []
        for input in device.inputs.values():
            tree[control.name][device.name].append(input.name)










#    engine.quit.connect(app.quit)
#    sys.exit(app.exec_())
