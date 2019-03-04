from PyQt5.QtCore import pyqtSignal, QObject

class DictSignal(QObject):
    signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.picklable = False

    def connect(self, func):
        self.signal.connect(func)

    def emit(self, state):
        self.signal.emit(state)


class FloatSignal(QObject):
    signal = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.picklable = False

    def connect(self, func):
        self.signal.connect(func)

    def emit(self, state):
        self.signal.emit(state)
