from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QHBoxLayout, QTableWidget, QCheckBox, QTabWidget, QLineEdit, QSlider)
from PyQt5.QtCore import *
from emergent.modules.parallel import ProcessHandler


class MonitorPanel(QVBoxLayout, ProcessHandler):
    def __init__(self, network, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.network = network
        self.parent = parent

        self.watchdogs = self.get_watchdogs()

        ''' Create table '''
        self.table = QTableWidget()
        self.table.setColumnCount(2)

        for hub in self.watchdogs:
            for w in self.watchdogs[hub].values():
                self.add_watchdog(w)

    def add_watchdog(self, watchdog):
        row = self.table.rowCount()
        self.insertRow(row)

        i = 0
        for col in ['name', 'state']:
            item = QTableWidgetItem(getattr(watchdog, col))
            item.setFlags(name_item.flags() ^ Qt.ItemIsEditable)
            self.setItem(row, 0, item)
            i += 1

    def get_watchdogs(self):
        self.watchdogs = {}
        for hub in self.network:
            self.watchdogs[hub.name] = hub.watchdogs
        return self.watchdogs
