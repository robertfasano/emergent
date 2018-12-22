''' This module implements a table to display the current state of defined
    Watchdog nodes. If no experiment is running, the user can right-click the
    node to check the state, which will also cause the Watchdog to react() if
    it is currently active. The threshold of each Watchdog is editable through the
    threshold column. '''


from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QHBoxLayout, QTableWidget, QMenu, QAction, QCheckBox, QTabWidget, QLineEdit, QSlider, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import *
from PyQt5.QtGui import QCursor
from emergent.modules.parallel import ProcessHandler

class ContextTable(QTableWidget):
    def __init__(self):
        QTableWidget.__init__(self)

        for i in range(5):
            self.insertColumn(i)
        self.setHorizontalHeaderLabels(['Watchpoint', 'State', 'Threshold', 'Value'])
        self.horizontalHeader().setMinimumSectionSize(75)

        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for i in range(1,4):
            self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)

        self.horizontalHeader().setFixedHeight(30)
        self.verticalHeader().hide()
        self.hideColumn(4)

        self.cellChanged.connect(self.update_threshold)

    def contextMenuEvent(self, event):
        self.menu = QMenu(self)
        self.action = QAction('Check')
        self.menu.addAction(self.action)
        self.menu.popup(QCursor.pos())

        pos = self.viewport().mapFromGlobal(QCursor.pos())
        row = self.rowAt(pos.y())
        item = self.item(row, 4)
        # print(item)
        self.action.triggered.connect(item.watchdog.check)

    def update_threshold(self, row, col):
        if col != 2:
            return
        try:
            self.item(row, 4).watchdog.threshold = float(self.item(row, col).text())
        except AttributeError:
            return

class MonitorLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, network, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.network = network
        self.parent = parent

        ''' Create table '''
        self.table = ContextTable()


        self.addWidget(self.table)

        self.update_table()

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

class CustomItem(QTableWidgetItem):
    def __init__(self, watchdog):
        super().__init__()
        self.watchdog = watchdog

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

        for col in ['name', 'state', 'threshold', 'value']:
            item = QTableWidgetItem(str(getattr(self.watchdog, col)))
            if col is not 'threshold':
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
            self.table.setItem(row, i, item)
            self.items[col] = item
            i += 1

        ''' Add hidden item to keep track of watchdog '''
        item = CustomItem(self.watchdog)
        item.setFlags(item.flags() ^ Qt.ItemIsEditable)
        self.table.setItem(row, i, item)

    def update(self, params):
        self.items['state'].setText(str(int(params['state'])))
        self.items['value'].setText('%.2f'%params['value'])
        self.items['threshold'].setText('%.2f'%params['threshold'])
