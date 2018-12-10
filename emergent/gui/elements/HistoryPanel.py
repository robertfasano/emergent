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
from emergent.gui.elements import ExperimentLayout, PlotWidget
from emergent.archetypes import Control, Device, Input
from emergent.signals import ActuateSignal, SettingsSignal
import functools
from emergent.archetypes.visualization import plot_2D, plot_1D
from emergent.archetypes import ProcessHandler
import matplotlib.pyplot as plt
import json
import itertools
import numpy as np

class OptimizerItem(QTableWidgetItem):
    def __init__(self, sampler, process_type):
        super().__init__()
        self.sampler = sampler
        self.process_type = process_type

class HistoryPanel(QVBoxLayout):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
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
        self.table.horizontalHeader().setStretchLastSection(True)


    def add_event(self, timestamp, experiment, event, status, sampler):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(str(timestamp)))
        self.table.setItem(row, 1, QTableWidgetItem(experiment))
        self.table.setItem(row, 2, QTableWidgetItem(event))
        self.table.setItem(row, 3, QTableWidgetItem(status))
        self.table.setItem(row, 4, OptimizerItem(sampler, status))

        return row

    def update_event_status(self, row, status):
        self.table.item(row, 3).setText(status)
        self.table.viewport().update()

    def on_double_click(self, row, col):
        sampler = self.table.item(row, 4).sampler
        process_type = self.table.item(row, 4).process_type
        algorithm = self.table.item(row, 2).text()
        self.popup = Visualizer(sampler, algorithm, self, row, process_type)
        # self.popup.show()

class Visualizer(QWidget, ProcessHandler):
    def __init__(self, sampler, algorithm, parent, row, process_type):
        super(Visualizer, self).__init__()
        QWidget().__init__()
        ProcessHandler.__init__(self)
        self.parent = parent
        self.sampler = sampler
        self.algorithm = algorithm
        self.process_type = process_type
        self.row = row
        with open('gui/stylesheet.txt',"r") as file:
            self.setStyleSheet(file.read())
        self.setWindowTitle('Experiment')
        self.sampler = sampler
        self.layout= QGridLayout()
        self.setLayout(self.layout)

        self.plot()

    def generate_figures(self):
        ''' Show cost vs time, parameters vs time, and parameters vs cost '''
        t, points, costs, errors = self.sampler.get_history(include_database = False)
        costs *= -1
        t = t.copy()-t[0]
        num_inputs = points.shape[1]
        control = self.sampler.parent

        ''' costs vs parameters '''
        fig, ax = plt.subplots(2,num_inputs, figsize=(10, 8))
        if num_inputs > 1:
            ax0 = ax[0]
        else:
            ax0 = ax
        ax0[0].set_ylabel(self.sampler.cost.__name__)
        cvp = {}
        for i in range(num_inputs):
            p = points[:,i]
            full_name =  self.sampler.history.columns[i]
            dev = full_name.split('.')[0]
            input = full_name.split('.')[1]
            limits = {full_name.replace('.', ': '): control.settings[dev][input]}
            # plot_1D(p, costs, limits=limits, cost_name = self.sampler.cost.__name__, ax = ax0[i])
            new_ax, fig = plot_1D(p, costs, limits=limits, cost_name = self.sampler.cost.__name__, errors = errors)
            cvp[full_name] = fig
            ax0[i].set_xlabel(full_name)

        ''' parameters vs time '''
        inputs = []
        pvt = {}
        for i in range(num_inputs):
            p = points[:,i]
            full_name =  self.sampler.history.columns[i]
            dev = full_name.split('.')[0]
            input = full_name.split('.')[1]
            inputs.append(full_name)
            limits = {full_name.replace('.', ': '): control.settings[dev][input]}
            name = list(limits.keys())[0]
            p = limits[name]['min'] + p*(limits[name]['max']-limits[name]['min'])

            if num_inputs == 1:
                cax = ax[1]
            else:
                cax = ax[1][i]
            # plot_1D(t, p, cost_name = self.sampler.cost.__name__, ax = cax)
            new_ax, fig = plot_1D(t, p, cost_name = self.sampler.cost.__name__, xlabel = 'Time (s)', ylabel = full_name, errors = errors)
            pvt[full_name] = fig
            cax.set_ylabel(full_name)
            cax.set_xlabel('Time (s)')

        ''' 2d plots '''

        axis_combos = list(itertools.combinations(range(num_inputs),2))
        fig2d = {}
        if self.process_type == 'optimize':
            for a in axis_combos:
                limits = {}
                full_names = []
                for ax in a:
                    full_name =  self.sampler.history.columns[ax]
                    full_names.append(full_name)
                    dev = full_name.split('.')[0]
                    input = full_name.split('.')[1]
                    limits[full_name.replace('.', ': ')] =  control.settings[dev][input]
                axis_combo_name = full_names[0] + '/' + full_names[1]
                p = points[:,a]
                fig2d[axis_combo_name] = plot_2D(p, costs, limits = limits)
        hist_fig = self.sampler.plot_optimization()
        return hist_fig, cvp, pvt, fig2d

    def plot(self):
        hist_fig, cvp, pvt, fig2d = self.generate_figures()
        inputs = list(cvp.keys())
        self.pw = PlotWidget(self, self.sampler, self.algorithm, inputs, hist_fig, cvp, pvt, fig2d, title='Visualizer: %s'%self.sampler.cost.__name__)
        self.pw.show()

    def check_progress(self):
        if not self.sampler.active:
            progress = 'Aborted'
        elif self.sampler.progress < 1:
            progress = '%.0f%%'%(self.sampler.progress*100)
        else:
            progress = 'Done'
        self.progress_label.setText(progress)
        self.result_label.setText(str(self.sampler.result))
        self.parent.update_event_status(self.row, progress)
