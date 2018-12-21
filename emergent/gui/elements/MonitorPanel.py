from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QHBoxLayout, QTableWidget, QCheckBox, QTabWidget, QLineEdit, QSlider, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import *
from emergent.modules.parallel import ProcessHandler


class MonitorLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, network, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.network = network
        self.parent = parent

        ''' Create table '''
        self.table = QTableWidget()
        for i in range(2):
            self.table.insertColumn(i)
        self.table.setHorizontalHeaderLabels(['Watchpoint', 'State'])
        self.table.horizontalHeader().setMinimumSectionSize(125)

        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setFixedHeight(25)
        self.table.verticalHeader().hide()

        self.addWidget(self.table)

        self.update_table()

        # self.update_delay = 1 # refresh rate in seconds
        #
        # self.update_timer = QTimer(self)
        # self.update_timer.timeout.connect(self.monitor)
        # self.update_timer.start(1000*self.update_delay)

    def update_table(self):
        self.watchdogs = self.get_watchdogs()
        self.watchdog_items = {}
        self.table.clearContents()
        for hub in self.watchdogs:
            self.watchdog_items[hub] = {}
            for w in self.watchdogs[hub].values():
                item = WatchdogItem(w, self.table)
                item.add()
                self.watchdog_items[hub][w.name] = item

    def get_watchdogs(self):
        self.watchdogs = {}
        for hub in self.network.hubs.values():
            self.watchdogs[hub.name] = hub.watchdogs
        return self.watchdogs

    def monitor(self):
        for hub in self.watchdogs:
            for w in self.watchdogs[hub].values():
                w._measure()

class WatchdogItem():
    def __init__(self, watchdog, table):
        self.watchdog = watchdog
        self.table = table
        self.watchdog.signal.connect(self.update)

    def add(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.items = {}
        i = 0
        for col in ['name', 'state']:
            item = QTableWidgetItem(str(getattr(self.watchdog, col)))
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
            self.table.setItem(row, i, item)
            self.items[col] = item
            i += 1

    def update(self, state):
        self.items['state'].setText(str(state))
