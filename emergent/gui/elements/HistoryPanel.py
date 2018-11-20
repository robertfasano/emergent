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
from emergent.gui.elements.ExperimentPanel import ExperimentLayout
from emergent.archetypes.node import Control, Device, Input, ActuateSignal, SettingsSignal
import functools
from emergent.archetypes.visualization import plot_2D, plot_1D
from emergent.archetypes.parallel import ProcessHandler
import matplotlib.pyplot as plt
import json
import itertools
import numpy as np

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
        self.layout.addWidget(QLabel(self.optimizer.sampler.cost_name), 0, 1)

        self.layout.addWidget(QLabel('Inputs:'), 1, 0)
        inputs_string = json.dumps(self.optimizer.sampler.inputs).replace('{', '').replace('}', '').replace('],', ']\n').replace('"', '')
        self.layout.addWidget(QLabel(inputs_string), 1,1)

        self.layout.addWidget(QLabel('Experiment parameters'), 2, 0)
        cost_params = self.optimizer.sampler.cost_params
        cost_params = str(cost_params).replace('{', '').replace(',', ',\n').replace('}', '')

        self.layout.addWidget(QLabel(cost_params), 2, 1)
        self.layout.addWidget(QLabel('Algorithm'), 3, 0)
        self.layout.addWidget(QLabel(algorithm), 3, 1)

        self.layout.addWidget(QLabel('Algorithm parameters'), 4, 0)
        params = self.optimizer.sampler.params
        params = str(params).replace('{', '').replace(',', ',\n').replace('}', '')
        self.layout.addWidget(QLabel(params), 4, 1)
        self.layout.addWidget(QLabel('Result'), 5, 0)
        try:
            result = str(self.optimizer.sampler.history['cost'].iloc[-1])
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
        ''' Show cost vs time, parameters vs time, and parameters vs cost '''
        t, points, costs = self.optimizer.sampler.get_history(include_database = self.use_database_checkbox.isChecked())
        t = t.copy()-t[0]
        num_inputs = points.shape[1]
        control = self.optimizer.parent

        ''' costs vs parameters '''
        fig, ax = plt.subplots(2,num_inputs, figsize=(10, 8))
        if num_inputs > 1:
            ax0 = ax[0]
        else:
            ax0 = ax
        ax0[0].set_ylabel(self.optimizer.cost.__name__)
        for i in range(num_inputs):
            p = points[:,i]
            full_name =  self.optimizer.sampler.history.columns[i]
            dev = full_name.split('.')[0]
            input = full_name.split('.')[1]
            limits = {full_name.replace('.', ': '): control.settings[dev][input]}
            plot_1D(p, costs, limits=limits, cost_name = self.optimizer.cost.__name__, ax = ax0[i])
            ax0[i].set_xlabel(full_name)

        ''' parameters vs time '''
        for i in range(num_inputs):
            p = points[:,i]
            full_name =  self.optimizer.sampler.history.columns[i]
            dev = full_name.split('.')[0]
            input = full_name.split('.')[1]
            limits = {full_name.replace('.', ': '): control.settings[dev][input]}
            name = list(limits.keys())[0]
            p = limits[name]['min'] + p*(limits[name]['max']-limits[name]['min'])

            if num_inputs == 1:
                cax = ax[1]
            else:
                cax = ax[1][i]
            plot_1D(t, p, cost_name = self.optimizer.cost.__name__, ax = cax)
            cax.set_ylabel(full_name)
            cax.set_xlabel('Time (s)')

        ''' 2d plots '''
        axis_combos = list(itertools.combinations(range(num_inputs),2))
        for a in axis_combos:
            limits = {}
            for ax in a:
                full_name =  self.optimizer.sampler.history.columns[ax]
                dev = full_name.split('.')[0]
                input = full_name.split('.')[1]
                limits[full_name.replace('.', ': ')] =  control.settings[dev][input]
            p = points[:,a]
            plot_2D(p, costs, limits = limits)
        # try:
        #     if points.shape[1] == 1:
        #         full_name =  self.optimizer.sampler.history.columns[0]
        #         dev = full_name.split('.')[0]
        #         input = full_name.split('.')[1]
        #         control = self.optimizer.parent
        #         limits = {full_name.replace('.', ': '): control.settings[dev][input]}
        #         plot_1D(points, costs, limits = limits, cost_name = self.optimizer.cost.__name__)
        #     elif points.shape[1] == 2:
        #         plot_2D(points, costs)
        # except Exception:
        #     pass
        # self.optimizer.plot_optimization()

    def check_progress(self):
        if not self.optimizer.active:
            progress = 'Aborted'
        elif self.optimizer.progress < 1:
            progress = '%.0f%%'%(self.optimizer.progress*100)
        else:
            progress = 'Done'
        self.progress_label.setText(progress)
        self.result_label.setText(str(self.optimizer.result))
        self.parent.update_event_status(self.row, progress)
