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
from emergent.archetypes.visualization import plot_2D
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
        # self.table.setCellWidget(row, 0, QLabel(str(timestamp)))
        # self.table.setCellWidget(row, 1, QLabel(experiment))
        # self.table.setCellWidget(row, 2, QLabel(event))
        # self.table.setCellWidget(row, 3, QLabel(status))
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
        self.popup = OptimizerPopup(optimizer, algorithm)
        self.popup.show()

class OptimizerPopup(QWidget):
    def __init__(self, optimizer, algorithm):
        super().__init__()
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
        self.layout.addWidget(QLabel(str(self.optimizer.history['cost'].iloc[-1])), 5, 1)



        self.plot_button = QPushButton('Plot')
        self.plot_button.clicked.connect(self.plot)
        self.layout.addWidget(self.plot_button, 6, 0)

    def plot(self):
        points, costs = self.optimizer.get_history()
        plot_2D(points, costs)
