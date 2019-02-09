''' The TaskPanel displays previously run Sampler instances with the time of execution,
    experiment, and algorithm (if applicable). Double clicking an item in the table
    opens a visualizer window defined in PlotWindow.py. '''

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import (QGridLayout,QTableView,QVBoxLayout, QWidget, QMenu,
                             QAction, QTableWidget, QTableWidgetItem, QFileDialog, QComboBox)
from PyQt5.QtCore import *
from emergent.gui.elements import PlotWidget
from emergent.utilities.plotting import plot_2D, plot_1D
import matplotlib.pyplot as plt
import itertools
import pickle

class ContextTable(QTableWidget):
    def __init__(self):
        QTableWidget.__init__(self)

        self.horizontalHeader().setFixedHeight(30)
        self.setColumnCount(5)
        for col in [4]:
            self.hideColumn(col)
        self.setHorizontalHeaderLabels(['Time', 'Experiment', 'Event', 'Active', 'Object'])
        self.horizontalHeader().setStretchLastSection(True)
        self.setStyleSheet('color:"#000000"; font-weight: light; font-family: "Exo 2"; font-size: 14px; background-color: rgba(255, 255, 255, 80%);')

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


class TaskPanel(QVBoxLayout):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.active_tasks = []
        self.table = ContextTable()
        self.table.cellDoubleClicked.connect(self.on_double_click)
        self.addWidget(self.table)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(lambda: self.update_visible_rows(''))
        self.update_timer.start(250)

        self.show_box = QComboBox()
        for item in ['All', 'Active', 'Inactive']:
            self.show_box.addItem(item)
        self.show_box.currentTextChanged.connect(self.update_visible_rows)
        self.addWidget(self.show_box)

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
        self.table.setItem(row, 3, QTableWidgetItem('True'))
        self.table.setItem(row, 4, SamplerItem(sampler, status))

        ''' Set row visibility based on self.show_box '''
        if self.show_box.currentText() == 'Inactive':
            self.table.setRowHidden(row, True)
        return row

    def check_active_rows(self):
        active_rows = []
        for r in range(self.table.rowCount()):
            active = self.table.item(r, 4).sampler.active
            if active:
                active_rows.append(r)
            self.table.setItem(r, 3, QTableWidgetItem(str(active)))
        return active_rows

    def hide_inactive(self, hide):
        for r in range(self.table.rowCount()):
            self.table.setRowHidden(r, False)
        active_rows = self.check_active_rows()
        for r in range(self.table.rowCount()):
            if r not in active_rows:
                self.table.setRowHidden(r, hide)

    def update_event_status(self, row, status):
        self.table.item(row, 3).setText(status)
        self.table.viewport().update()

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
        sampler = self.table.item(row, 4).sampler
        process_type = self.table.item(row, 4).process_type
        algorithm = self.table.item(row, 2).text()
        self.popup = Visualizer(sampler, self, row, process_type)

    def load_task(self):
        self.fileWidget = QWidget()
        filename = QFileDialog.getOpenFileName(self.fileWidget, 'Open experiment', self.parent.network.path['data'], 'Samplers (*.sci)')[0]
        with open(filename, 'rb') as f:
            sampler = pickle.load(f)
        self.add_event(sampler)

class Visualizer(QWidget):
    def __init__(self, sampler, parent, row, process_type):
        super(Visualizer, self).__init__()
        QWidget().__init__()
        self.parent = parent
        self.sampler = sampler
        self.process_type = process_type
        self.row = row
        self.sampler = sampler
        self.layout= QGridLayout()
        self.setLayout(self.layout)

        cost_vs_param, param_vs_time = self.generate_figures()
        self.pw = PlotWidget(self, self.sampler, cost_vs_param, param_vs_time, title='Visualizer: %s'%self.sampler.experiment.__name__)
        self.pw.show()

    def generate_figures(self):
        ''' Show cost vs time, parameters vs time, and parameters vs cost '''
        t, points, costs, errors = self.sampler.get_history(include_database = False)
        costs *= -1
        t = t.copy()-t[0]
        if points is None:
            num_inputs = 0
        else:
            num_inputs = points.shape[1]
        hub = self.sampler.hub
        cost_vs_param = None
        param_vs_time = None
        if num_inputs > 0:
            ''' costs vs parameters '''
            fig, ax = plt.subplots(2,num_inputs, figsize=(10, 8))
            if num_inputs > 1:
                ax0 = ax[0]
            else:
                ax0 = ax
            ax0[0].set_ylabel(self.sampler.experiment.__name__)
            cost_vs_param = {}
            for i in range(num_inputs):
                p = points[:,i]
                name =  self.sampler.history.columns[i].replace('.', ': ')
                limits = {name: self.sampler.get_limits()[name]}
                new_ax, fig = plot_1D(p, costs, limits=limits, cost_name = self.sampler.experiment.__name__, errors = errors)
                cost_vs_param[self.sampler.history.columns[i]] = fig
                ax0[i].set_xlabel(self.sampler.history.columns[i])

            ''' parameters vs time '''
            param_vs_time = {}
            for i in range(num_inputs):
                p = points[:,i]
                name =  self.sampler.history.columns[i].replace('.', ': ')
                limits = self.sampler.get_limits()
                p = limits[name]['min'] + p*(limits[name]['max']-limits[name]['min'])

                if num_inputs == 1:
                    cax = ax[1]
                else:
                    cax = ax[1][i]
                new_ax, fig = plot_1D(t, p, cost_name = self.sampler.experiment.__name__, xlabel = 'Time (s)', ylabel = self.sampler.history.columns[i], errors = errors)
                param_vs_time[self.sampler.history.columns[i]] = fig
                cax.set_ylabel(self.sampler.history.columns[i])
                cax.set_xlabel('Time (s)')

        ''' 2d plots '''

        # axis_combos = list(itertools.combinations(range(num_inputs),2))
        # fig2d = {}
        # if self.process_type == 'optimize':
        #     for a in axis_combos:
        #         limits = {}
        #         full_names = []
        #         for ax in a:
        #             full_name =  self.sampler.history.columns[ax]
        #             full_names.append(full_name)
        #             thing = full_name.split('.')[0]
        #             input = full_name.split('.')[1]
        #             limits[full_name.replace('.', ': ')] =  hub.settings[thing][input]
        #         axis_combo_name = full_names[0] + '/' + full_names[1]
        #         p = points[:,a]
        #         fig2d[axis_combo_name] = plot_2D(p, costs, limits = limits)


        return cost_vs_param, param_vs_time

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
