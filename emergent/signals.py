from PyQt5.QtCore import pyqtSignal, QObject

class ProcessSignal(QObject):
    signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

    def connect(self, func):
        self.signal.connect(func)

    def emit(self, state):
        self.signal.emit(state)

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

    def emit(self, hub, thing, input):
        self.signal.emit({'hub':hub, 'thing':thing, 'input':input})

class RemoveSignal(QObject):
    signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

    def connect(self, func):
        self.signal.connect(func)

    def emit(self, hub, thing, input):
        self.signal.emit({'hub':hub, 'thing':thing, 'input':input})

class WatchdogSignal(QObject):
    signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

    def connect(self, func):
        self.signal.connect(func)

    def emit(self, state):
        self.signal.emit(state)
