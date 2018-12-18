#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
import sys
import types
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont, QWindow, QCursor
from PyQt5.QtWidgets import (QApplication, QAbstractItemView,QCheckBox, QComboBox, QGridLayout,
        QGroupBox, QHBoxLayout, QGridLayout, QLabel, QTextEdit, QTreeView, QPushButton, QTableView,QVBoxLayout,
        QWidget, QMenu, QAction, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem, QDialog, QFileDialog)
from PyQt5.QtCore import *
import json
from emergent.gui.elements import ExperimentLayout, PlotWidget
from emergent.modules import Hub, Thing, Input
import functools
from emergent.modules.visualization import plot_2D, plot_1D
from emergent.modules import ProcessHandler
import matplotlib.pyplot as plt
import json
import itertools
import numpy as np
import pickle

class ContextTable(QTableWidget):
    def __init__(self):
        QTableWidget.__init__(self)

        self.horizontalHeader().setFixedHeight(30)
        self.setColumnCount(5)
        for col in [3, 4]:
            self.hideColumn(col)
        self.setHorizontalHeaderLabels(['Time', 'Experiment', 'Event', 'Status', 'Object'])
        self.horizontalHeader().setStretchLastSection(True)

    def contextMenuEvent(self, event):
        self.menu = QMenu(self)
        self.action = QAction('Terminate')
        self.menu.addAction(self.action)
        self.menu.popup(QCursor.pos())

        pos = self.viewport().mapFromGlobal(QCursor.pos())
        row = self.rowAt(pos.y())
        name = self.item(row, 0).text()
        sampler = self.item(row, 4).sampler
        self.action.triggered.connect(sampler.terminate)


class SamplerItem(QTableWidgetItem):
    def __init__(self, sampler, process_type):
        super().__init__()
        self.sampler = sampler
        self.process_type = process_type



class HistoryPanel(QVBoxLayout):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        # self.addWidget(QLabel('Tasks'))
        self.table = ContextTable()
        self.table.cellDoubleClicked.connect(self.on_double_click)
        self.addWidget(self.table)

    def add_event(self, sampler, status = ''):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(sampler.start_time))
        self.table.setItem(row, 1, QTableWidgetItem(sampler.experiment_name))
        if sampler.algorithm is not None:
            algorithm_name = sampler.algorithm.name
        else:
            algorithm_name = 'Run'
        self.table.setItem(row, 2, QTableWidgetItem(algorithm_name))
        self.table.setItem(row, 3, QTableWidgetItem(status))
        self.table.setItem(row, 4, SamplerItem(sampler, status))

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

    def load_task(self):
        self.fileWidget = QWidget()
        filename = QFileDialog.getOpenFileName(self.fileWidget, 'Open experiment', self.parent.network.data_path, 'Samplers (*.sci)')[0]
        with open(filename, 'rb') as f:
            sampler = pickle.load(f)
        self.add_event(sampler)

class Visualizer(QWidget):
    def __init__(self, sampler, algorithm, parent, row, process_type):
        super(Visualizer, self).__init__()
        QWidget().__init__()
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
        hub = self.sampler.hub

        ''' costs vs parameters '''
        fig, ax = plt.subplots(2,num_inputs, figsize=(10, 8))
        if num_inputs > 1:
            ax0 = ax[0]
        else:
            ax0 = ax
        ax0[0].set_ylabel(self.sampler.experiment.__name__)
        cvp = {}
        for i in range(num_inputs):
            p = points[:,i]
            full_name =  self.sampler.history.columns[i]
            thing = full_name.split('.')[0]
            input = full_name.split('.')[1]
            limits = {full_name.replace('.', ': '): hub.settings[thing][input]}
            # plot_1D(p, costs, limits=limits, cost_name = self.sampler.experiment.__name__, ax = ax0[i])
            new_ax, fig = plot_1D(p, costs, limits=limits, cost_name = self.sampler.experiment.__name__, errors = errors)
            cvp[full_name] = fig
            ax0[i].set_xlabel(full_name)

        ''' parameters vs time '''
        inputs = []
        pvt = {}
        for i in range(num_inputs):
            p = points[:,i]
            full_name =  self.sampler.history.columns[i]
            thing = full_name.split('.')[0]
            input = full_name.split('.')[1]
            inputs.append(full_name)
            limits = {full_name.replace('.', ': '): hub.settings[thing][input]}
            name = list(limits.keys())[0]
            p = limits[name]['min'] + p*(limits[name]['max']-limits[name]['min'])

            if num_inputs == 1:
                cax = ax[1]
            else:
                cax = ax[1][i]
            # plot_1D(t, p, cost_name = self.sampler.experiment.__name__, ax = cax)
            new_ax, fig = plot_1D(t, p, cost_name = self.sampler.experiment.__name__, xlabel = 'Time (s)', ylabel = full_name, errors = errors)
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
                    thing = full_name.split('.')[0]
                    input = full_name.split('.')[1]
                    limits[full_name.replace('.', ': ')] =  hub.settings[thing][input]
                axis_combo_name = full_names[0] + '/' + full_names[1]
                p = points[:,a]
                fig2d[axis_combo_name] = plot_2D(p, costs, limits = limits)
        hist_fig = self.sampler.plot_optimization()
        return hist_fig, cvp, pvt, fig2d

    def plot(self):
        hist_fig, cvp, pvt, fig2d = self.generate_figures()
        inputs = list(cvp.keys())
        self.pw = PlotWidget(self, self.sampler, self.algorithm, inputs, hist_fig, cvp, pvt, fig2d, title='Visualizer: %s'%self.sampler.experiment.__name__)
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
