''' The TaskPanel displays previously run Sampler instances with the time of execution,
    experiment, and algorithm (if applicable). Double clicking an item in the table
    opens a visualizer window defined in PlotWindow.py. '''

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import (QGridLayout,QTableView,QVBoxLayout, QWidget, QMenu,
                             QAction, QTableWidget, QTableWidgetItem, QFileDialog, QComboBox)
from PyQt5.QtCore import *
from emergent.dashboard.gui import PlotWidget
from emergent.utilities.plotting import plot_2D, plot_1D
from emergent.utilities.signals import DictSignal
import matplotlib.pyplot as plt
import itertools
import pickle
import json
import pandas as pd
import numpy as np

class ContextTable(QTableWidget):
    def __init__(self, parent):
        QTableWidget.__init__(self)
        self.parent = parent
        self.horizontalHeader().setFixedHeight(30)
        self.setColumnCount(6)
        for col in [4, 5]:
            self.hideColumn(col)
        self.setHorizontalHeaderLabels(['Time', 'Experiment', 'Event', 'Active', 'ID', 'Hub'])
        self.horizontalHeader().setStretchLastSection(True)
        self.setStyleSheet('color:"#000000"; font-weight: light; font-family: "Exo 2"; font-size: 14px; background-color: rgba(255, 255, 255, 80%);')

    def contextMenuEvent(self, event):
        self.menu = QMenu(self)
        self.action = QAction('Terminate')
        self.menu.addAction(self.action)
        self.check_action = QAction('Check')
        self.menu.addAction(self.check_action)
        pos = self.viewport().mapFromGlobal(QCursor.pos())
        row = self.rowAt(pos.y())
        name = self.item(row, 0).text()
        self.id = self.item(row, 4).text()
        self.hub = self.item(row, 5).text()
        self.check_action.triggered.connect(self.check)
        self.action.triggered.connect(self.terminate)
        self.menu.popup(QCursor.pos())

    def check(self):
        active = self.parent.dashboard.get('hubs/%s/samplers/%s/active'%(self.hub, self.id))
        return active

    def terminate(self):
        self.parent.dashboard.post('hubs/%s/samplers/%s/active'%(self.hub, self.id), {'status': 0})

class TaskPanel(QVBoxLayout):
    def __init__(self, dashboard):
        super().__init__()
        self.dashboard = dashboard
        self.active_tasks = []
        self.table = ContextTable(self)
        self.table.cellDoubleClicked.connect(self.on_double_click)
        self.addWidget(self.table)

        self.show_box = QComboBox()
        for item in ['All', 'Active', 'Inactive']:
            self.show_box.addItem(item)
        self.show_box.currentTextChanged.connect(self.update_visible_rows)
        self.addWidget(self.show_box)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(lambda: self.update_visible_rows(''))

        self.signal = DictSignal()
        self.signal.connect(self._add_event)

        self.load_master_tasks()

    def add_event(self, event):
        self.signal.emit(event)

    def _add_event(self, event, status = ''):
        self.update_timer.start(250)
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(event['start time']))
        self.table.setItem(row, 1, QTableWidgetItem(event['experiment']))
        if 'algorithm' in event:
            algorithm_name = event['algorithm']
        else:
            algorithm_name = 'Measure'

        self.table.setItem(row, 2, QTableWidgetItem(algorithm_name))
        self.table.setItem(row, 3, QTableWidgetItem('True'))
        self.table.setItem(row, 4, QTableWidgetItem(event['id']))
        self.table.setItem(row, 5, QTableWidgetItem(event['hub']))

        ''' Set row visibility based on self.show_box '''
        if self.show_box.currentText() == 'Inactive':
            self.table.setRowHidden(row, True)
        return row

    def check_active_rows(self):
        active_rows = []
        active_ids = {}
        for r in range(self.table.rowCount()):
            id = self.table.item(r, 4).text()
            hub = self.table.item(r, 5).text()
            if hub not in active_ids:
                active_ids[hub] = self.dashboard.get('hubs/%s/samplers/active'%hub)
            active = id in active_ids[hub]
            if active:
                active_rows.append(r)
            self.table.setItem(r, 3, QTableWidgetItem(str(active)))
        if len(active_rows) == 0:
            self.update_timer.stop()
        return active_rows

    def load_master_tasks(self):
        tasks = self.dashboard.get('tasks')
        for t in tasks:
            self._add_event(self.dashboard.get('tasks/%s'%t))

    def update_visible_rows(self, text):
        text = self.show_box.currentText()
        for r in range(self.table.rowCount()):
            self.table.setRowHidden(r, False)

        active_rows = self.check_active_rows()
        for r in range(self.table.rowCount()):
            if r not in active_rows:
                if text == 'Active':
                    self.table.setRowHidden(r, True)
            else:
                if text == 'Inactive':
                    self.table.setRowHidden(r, True)

    def on_double_click(self, row, col):
        id = self.table.item(row, 4).text()
        hub = self.table.item(row, 5).text()
        self.visualizer = Visualizer(hub, id, self)


class Visualizer(QWidget):
    def __init__(self, hub, sampler_id, parent):
        ''' sampler: a JSON with the following fields:
                experiment_name
                t
                points
                costs
                errors
                limits
        '''
        super().__init__()
        self.sampler_id = sampler_id
        self.parent = parent
        self.hub = hub

        cost_vs_param, param_vs_time = self.generate_figures(hub)
        self.pw = PlotWidget(hub, self.sampler_id, cost_vs_param, param_vs_time, self)
        self.pw.show()

    def df_to_arrays(self, history):
        ''' Return a multidimensional array and corresponding points from the history df'''
        arrays = []
        state = {}
        costs = history['cost'].values
        errors = None
        if 'error' in history.columns:
            errors = history['error'].values
            if np.isnan(errors).any():
                errors = None
        t = history.index.values
        for col in history.columns:
            if col not in ['cost', 'error']:
                arrays.append(history[col].values)
                thing = col.split(':')[0]
                knob = col.split(':')[1]
                if thing not in state.keys():
                    state[thing] = {}
                state[thing][knob] = 0
        if len(arrays) > 0:
            points = np.vstack(arrays).T.astype(float)
        else:
            points = None
        costs = costs.astype(float)

        return t, points, costs, errors

    def generate_figures(self, hub):
        ''' Show cost vs time, parameters vs time, and parameters vs cost '''
        history = self.parent.dashboard.get('hubs/%s/samplers/%s/data'%(hub, self.sampler_id))['history']
        history = pd.read_json(history)
        params = self.parent.dashboard.get('hubs/%s/samplers/%s/parameters'%(hub, self.sampler_id))

        t, points, costs, errors = self.df_to_arrays(history)
        costs *= -1
        t = t.copy()-t[0]
        if points is None:
            num_knobs = 0
        else:
            num_knobs = points.shape[1]
        cost_vs_param = None
        param_vs_time = None
        if num_knobs > 0:
            ''' costs vs parameters '''
            fig, ax = plt.subplots(2,num_knobs, figsize=(10, 8))
            if num_knobs > 1:
                ax0 = ax[0]
            else:
                ax0 = ax
            ax0[0].set_ylabel(params['experiment']['name'])
            cost_vs_param = {}

            for i in range(num_knobs):
                p = points[:,i]
                name =  history.columns[i]
                thing = history.columns[i].split(':')[0]
                knob = history.columns[i].split(':')[1]
                limits = {name: params['limits'][thing][knob]}
                new_ax, fig = plot_1D(p, costs, limits=limits, cost_name = params['experiment']['name'], errors = errors)
                cost_vs_param[history.columns[i]] = fig
                ax0[i].set_xlabel(history.columns[i])

            ''' parameters vs time '''
            param_vs_time = {}
            for i in range(num_knobs):
                p = points[:,i]
                name =  history.columns[i]
                thing = history.columns[i].split(':')[0]
                knob = history.columns[i].split(':')[1]
                limits = params['limits']
                p = limits[thing][knob]['min'] + p*(limits[thing][knob]['max']-limits[thing][knob]['min'])

                if num_knobs == 1:
                    cax = ax[1]
                else:
                    cax = ax[1][i]
                new_ax, fig = plot_1D(t, p, cost_name = params['experiment']['name'], xlabel = 'Time (s)', ylabel = history.columns[i], errors = errors)
                param_vs_time[history.columns[i]] = fig
                cax.set_ylabel(history.columns[i])
                cax.set_xlabel('Time (s)')

        return cost_vs_param, param_vs_time

    def plot_optimization(self, history, name):
        ''' Plots an optimization time series stored in self.history. '''
        t, points, costs, errors = self.df_to_arrays(history)
        t = t.copy() - t[0]
        ax, fig = plot_1D(t,
                          -costs,
                          errors=errors,
                          xlabel='Time (s)',
                          ylabel=name)

        return fig
