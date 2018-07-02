from PyQt5.QtCore import QObject, pyqtProperty, Q_ARG, QVariant, pyqtSlot
import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-1]))
import json
import inspect

class Link(QObject):
    ''' This class bridges the gap between device-facing code (written in Python and independent of the GUI)
        and user-facing code (written in QML and independent of the device). '''

    def __init__(self, name, engine):
        QObject.__init__(self)
        self.name = name
        self.engine = engine

        ''' Register the object in the context of QML '''
        self.engine.rootContext().setContextProperty(self.name, self)
        if hasattr(self.engine, 'hubs'):
            self.engine.hubs.append(self)
        else:
            self.engine.hubs = [self]
        ''' Define properties '''
        self._property1 = 0


    def _retrieve_handles(self, item = 'Sidebar'):
        ''' Retrieve handle for appropriate element. For example, the GUI element for the coils is called
            coilElement and is a child of the ApplicationWindow. '''
        self.element = self.engine.rootObjects()[0].findChildren(QObject, self.name+"Hub")[0]
        self.elementMetaObject = self.element.metaObject()

#        print( self.element.findChildren(QObject, self.name+item))
#        self.sidebar = self.element.findChildren(QObject, self.name+item)[0]
        self.sidebar = self.element.findChildren(QObject, 'Sidebar')[0]

        self.metaObject = self.sidebar.metaObject()

        ''' Retrieve handle for the clickable, allowing us to hide it if the device connection fails '''
        self.clickable = self.element.findChildren(QObject, 'Clickable')[0]
        self.clickable.setProperty('connected', True)

        ''' Retrieve handle for the listModel, allowing dynamic updating '''
        self.listModel = self.element.findChildren(QObject, 'Model')[0]
        self.listMetaObject = self.listModel.metaObject()

        ''' Retrieve handle for the popup, allowing function information '''
        self.popup = self.sidebar.findChildren(QObject, 'Popup')[0]
        self.popup_model = self.popup.findChildren(QObject, 'Model')[0]
        self.popupModelMetaObject = self.popup_model.metaObject()

        self.executor = self.sidebar.findChildren(QObject, 'Executor')[0]
        self.executor_model = self.executor.findChildren(QObject, 'Model')[0]
        self.executorModelMetaObject = self.executor_model.metaObject()

    def _append_listModel(self, name, value, device):
        d = {"name": name, "value": value, "device": device}
        self.elementMetaObject.invokeMethod(self.element, "append", Q_ARG(QVariant, d))

    ''' Here is an example of a getter method. When the child of the Link class is registered with QML, then
        QML can access the Python variable link._property1 via the QML property link.property1 '''
    @pyqtProperty(float)
    def property1(self):
        return self._property1

    ''' Here is an example of a setter method. QML can update the Python variable link._property1 by
        executing link.property1 = value '''
    @property1.setter
    def property1(self, property1):
        self._property1 = property1

    ''' The previous setter only works if the property is hardcoded in QML. If instead we want to change a Python
        variable given the string property1 in QML (e.g. when working with ListModels), we need to go through Python's
        setattr function. For example, in QML one can execute link.set_attr("property1", 0) to set the Python variable
        link._property1 to zero.'''
    @pyqtSlot(str, str)

    def _set_attr(self, string, value, update_device = True):
        setattr(self, '_'+string, value)
#        print('Updating attribute to %s'%(getattr(self, '_'+string)))

    ''' The _change_value method lets us push changes from Python to QML instead of requesting them in QML. '''
    def _change_value(self, target, value):
        ''' Updates the value of the ListElement with name str target to QVariant value '''
        value = float(value)
        self.metaObject.invokeMethod(self.sidebar, "change_value", Q_ARG(QVariant, target), Q_ARG(QVariant, value))

    def _populate_listModel(self):
        for device in self.params.keys():
            if hasattr(self._get_device(device), 'mirrors'):
                code = -1113
            elif hasattr(self._get_device(device), 'labjack'):
                code = -1112
            else:
                code = -1111
            self._append_listModel(device, code, device)

            for param in self.params[device].keys():
                if self.params[device][param]['gui']:
                    self._append_listModel(param.replace('_', ' '), self.params[device][param]['value'], device)

    @pyqtSlot(str, str, str)
    def _set_param(self, target, value, device, update_device = True):
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
        for dev in self.devices:
            if dev.name == device:
                getattr(dev, func)()

    @pyqtSlot(str)
    def _refresh(self, target):
        print('Refreshing %s'%target)
        for dev in self.devices:
            if dev.name == target:
                dev._connect()

    @pyqtSlot(str)
    def _list_methods(self, name):
        for dev in self.devices:
            if dev.name == name:
                methods = [func for func in dir(dev) if callable(getattr(dev, func)) and not func.startswith("_")]
                self.popupModelMetaObject.invokeMethod(self.popup, "clear")
                for m in methods:
                    d = {"name": m, "device": dev.name}
                    self.popupModelMetaObject.invokeMethod(self.popup, "append", Q_ARG(QVariant, d))

    @pyqtSlot(str, str)
    def _list_args(self, device, function):
        for dev in self.devices:
            if dev.name == device:
                f = getattr(dev, function)
                args = inspect.signature(f).parameters
                args = list(args.items())
                names = []
                defaults = []
                self.executorModelMetaObject.invokeMethod(self.executor, "clear")

                for a in args:
                    name = a[0]
                    default = str(a[1])
                    if default == name:
                        default = ''
                    else:
                        default = default.split('=')[1]
                    d = {"name": name, "value": default}
                    self.executorModelMetaObject.invokeMethod(self.executor, "append", Q_ARG(QVariant, d))
