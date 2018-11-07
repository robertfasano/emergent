#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
import sys
import types
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont, QWindow
from PyQt5.QtWidgets import (QApplication, QAbstractItemView,QCheckBox, QComboBox, QGridLayout,
        QGroupBox, QHBoxLayout, QGridLayout, QLabel, QTextEdit, QTreeView, QPushButton, QTableView,QVBoxLayout,
        QWidget, QMenu, QAction, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem, QDialog)
from PyQt5.QtCore import *
import json
from emergent.archetypes.optimizer import Optimizer
from emergent.gui.elements.ExperimentPanel import OptimizerLayout
from emergent.archetypes.node import Control, Device, Input, ActuateSignal, SettingsSignal
import functools
from emergent.archetypes.visualization import plot_2D, plot_1D
from emergent.archetypes.parallel import ProcessHandler

import json
class OptimizerItem(QTableWidgetItem):
    def __init__(self, optimizer):
        super().__init__()
        self.optimizer = optimizer

class HistoryPanel(QVBoxLayout):
    def __init__(self):
        super().__init__()
        self.addWidget(QLabel('Tasks'))
        self.table = QTableWidget()
        self.addWidget(self.table)
        self.table.insertColumn(0)
        self.table.insertColumn(1)
        self.table.insertColumn(2)
        self.table.insertColumn(3)
        self.table.insertColumn(4)
        # self.table.setColumnCount(5)
        self.table.hideColumn(4)
        self.table.setHorizontalHeaderLabels(['Time', 'Experiment', 'Event', 'Status', 'Object'])
        self.table.cellDoubleClicked.connect(self.on_double_click)


    def add_event(self, timestamp, experiment, event, status, optimizer):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(str(timestamp)))
        self.table.setItem(row, 1, QTableWidgetItem(experiment))
        self.table.setItem(row, 2, QTableWidgetItem(event))
        self.table.setItem(row, 3, QTableWidgetItem(status))
        self.table.setItem(row, 4, OptimizerItem(optimizer))

        return row

    def update_event_status(self, row, status):
        self.table.item(row, 3).setText(status)
        self.table.viewport().update()

    def on_double_click(self, row, col):
        optimizer = self.table.item(row, 4).optimizer
        algorithm = self.table.item(row, 2).text()
        self.popup = OptimizerPopup(optimizer, algorithm, self, row)
        self.popup.show()

class OptimizerPopup(QWidget, ProcessHandler):
    def __init__(self, optimizer, algorithm, parent, row):
        super(OptimizerPopup, self).__init__()
        QWidget().__init__()
        ProcessHandler.__init__(self)
        self.parent = parent
        self.row = row
        with open('gui/stylesheet.txt',"r") as file:
            self.setStyleSheet(file.read())
        self.optimizer = optimizer
        self.layout= QGridLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(QLabel('Experiment:'), 0, 0)
        self.layout.addWidget(QLabel(self.optimizer.cost_name), 0, 1)

        self.layout.addWidget(QLabel('Experiment parameters'), 1, 0)
        cost_params = self.optimizer.cost_params
        cost_params = str(cost_params).replace('{', '').replace(',', ',\n').replace('}', '')

        self.layout.addWidget(QLabel(cost_params), 1, 1)
        self.layout.addWidget(QLabel('Algorithm'), 2, 0)
        self.layout.addWidget(QLabel(algorithm), 2, 1)

        self.layout.addWidget(QLabel('Algorithm parameters'), 3, 0)
        params = self.optimizer.params
        params = str(params).replace('{', '').replace(',', ',\n').replace('}', '')
        self.layout.addWidget(QLabel(params), 3, 1)
        self.layout.addWidget(QLabel('Result'), 5, 0)
        try:
            result = str(self.optimizer.history['cost'].iloc[-1])
        except IndexError:
            result = ''
        self.result_label = QLabel(result)
        self.layout.addWidget(self.result_label, 5, 1)

        self.layout.addWidget(QLabel('Progress:'), 6, 0)
        self.progress_label = QLabel(str(self.optimizer.progress))
        self.layout.addWidget(self.progress_label, 6, 1)

        self.use_database_checkbox = QCheckBox()
        self.layout.addWidget(QLabel('Include database in plot'), 7, 0)
        self.layout.addWidget(self.use_database_checkbox, 7, 1)
        self.terminate_button = QPushButton('Terminate')
        self.terminate_button.clicked.connect(self.optimizer.terminate)
        self.layout.addWidget(self.terminate_button, 8, 0)

        self.plot_button = QPushButton('Plot result')
        self.plot_button.clicked.connect(self.plot)
        self.layout.addWidget(self.plot_button, 8, 1)

        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.check_progress)
        self.progress_timer.start(100)

    def plot(self):
        points, costs = self.optimizer.get_history(include_database = self.use_database_checkbox.isChecked())
        if points.shape[1] == 1:
            full_name =  self.optimizer.history.columns[0]
            dev = full_name.split('.')[0]
            input = full_name.split('.')[1]
            control = self.optimizer.parent
            limits = {full_name.replace('.', ': '): control.settings[dev][input]}
            plot_1D(points, costs, limits = limits)
        elif points.shape[1] == 2:
            plot_2D(points, costs)

    def check_progress(self):
        self.progress_label.setText('%.0f%%'%(self.optimizer.progress*100))
        self.result_label.setText(str(self.optimizer.result))

        if not self.optimizer.active:
            self.parent.update_event_status(self.row, 'Done')
