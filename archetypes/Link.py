from PyQt5.QtCore import QObject, pyqtProperty, Q_ARG, QVariant, pyqtSlot
import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-1]))
import json
import inspect
from emergent.archetypes.node import Control

class Link(QObject):
    ''' This class bridges the gap between device-facing code (written in Python and independent of the GUI)
        and user-facing code (written in QML and independent of the device). '''

    def __init__(self, engine):
        ''' Initializes the link and registers with the given name inside the
            QML engine. '''
        QObject.__init__(self)
        self.engine = engine

        ''' Register the object in the context of QML '''
        self.engine.rootContext().setContextProperty('link', self)

    def _retrieve_handles(self, item = 'Sidebar'):
        ''' Retrieve handle for appropriate element. For example, the GUI element for the coils is called
            coilElement and is a child of the ApplicationWindow. '''
        self.list = self.engine.rootObjects()[0].findChildren(QObject, "list")[0]
        self.listMetaObject = self.list.metaObject()

        self.sidebar = self.element.findChildren(QObject, 'Sidebar')[0]
        self.metaObject = self.sidebar.metaObject()

    def _append_listModel(self, name):
        ''' Appends a device to the DeviceBrowser ListModel. '''
        d = {"name": name}
        self.listMetaObject.invokeMethod(self.element, "append", Q_ARG(QVariant, d))

    def _populate_listModel(self):
        ''' Collects all declared Control nodes and creates ListElements in the GUI for each. Adds sublists for each Device, with further sublists for each Input. '''
        for control in Control.instances():
            self._append_listModel(control.name)
            self._add_subList()
            for device in control.devices:
                self._add_subListElement(device.name)

    @pyqtSlot(str, str, str)
    def _set_param(self, target, value, device, update_device = True):
        ''' Allows QML-instantiated param updates pushed to target device. '''
        value = float(value)
        target = target.replace(' ', '_')
        index = self.params[device][target]['index']

        if index != None and update_device:
            print('Updating %s to %f'%(target, value))
            target_state = self.state.copy()
            target_state[index] = value
            self.actuate(target_state)

    @pyqtSlot(str, str)
    def _call_device_function(self, device, func):
        ''' Allows QML-instantiated function calls on a target child device. '''
        dev = self._get_device(device)
        getattr(dev, func)()

    @pyqtSlot(str)
    def _refresh(self, target):
        ''' Attempts to reconnect to the target child device. '''
        print('Refreshing %s'%target)
        dev = self._get_device(target)
        dev._connect()

    @pyqtSlot(str)
    def _list_methods(self, name):
        ''' Populates the QML FunctionBrowser for the targeted device. '''
        dev = self._get_device(name)
        methods = [func for func in dir(dev) if callable(getattr(dev, func)) and not func.startswith("_")]
        self.popupModelMetaObject.invokeMethod(self.popup, "clear")
        for m in methods:
            d = {"name": m, "device": dev.name}
            self.popupModelMetaObject.invokeMethod(self.popup, "append", Q_ARG(QVariant, d))

    @pyqtSlot(str, str)
    def _list_args(self, device, function):
        ''' Displays docstring and args for the targeted device and function. '''
        dev = self._get_device(device)
        f = getattr(dev, function)
        args = inspect.signature(f).parameters
        args = list(args.items())
        names = []
        defaults = []
        doc = {'text':inspect.getdoc(f)}
        if doc['text'] is None:
            doc['text'] = 'None'
        self.popupModelMetaObject.invokeMethod(self.popup, "set_docs", Q_ARG(QVariant, doc))
        self.popupModelMetaObject.invokeMethod(self.popup, "clear_args")
        for a in args:
            name = a[0]
            default = str(a[1])
            if default == name:
                default = 'Enter'
            else:
                default = default.split('=')[1]
            d = {"name": name, "value": default}
            self.popupModelMetaObject.invokeMethod(self.popup, "append_args", Q_ARG(QVariant, d))
