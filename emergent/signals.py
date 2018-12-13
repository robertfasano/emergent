from PyQt5.QtCore import pyqtSignal, QObject

class ActuateSignal(QObject):
    signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

    def connect(self, func):
        self.signal.connect(func)

    def emit(self, state):
        self.signal.emit(state)


class CreateSignal(QObject):
    signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

    def connect(self, func):
        self.signal.connect(func)

    def emit(self, control, device, input):
        self.signal.emit({'control':control, 'device':device, 'input':input})

class RemoveSignal(QObject):
    signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

    def connect(self, func):
        self.signal.connect(func)

    def emit(self, control, device, input):
        self.signal.emit({'control':control, 'device':device, 'input':input})
