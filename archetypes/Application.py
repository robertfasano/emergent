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

''' Gather nodes '''
controls = Control.instances
for control in controls:
    devices.append(control.devices)
    for device in devices:
    

''' Show window '''
engine.load("gui/main.qml")                     # Load the qml file into the engine
window = engine.rootObjects()[0]
window.show()

''' Retrieve element handles from the engine and initialize default values '''
for hub in engine.hubs:
    hub._retrieve_handles()
    hub._populate_listModel()






#    engine.quit.connect(app.quit)
#    sys.exit(app.exec_())
