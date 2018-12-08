from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QScrollArea, QProgressBar, QTableWidgetItem, QTableWidget, qApp, QHBoxLayout, QCheckBox, QTabWidget, QLineEdit, QSlider, QGridLayout)
from PyQt5.QtCore import *
from emergent.archetypes.parallel import ProcessHandler
from emergent.archetypes.optimizer import Optimizer
import inspect
import datetime
import json
import logging as log

class OptimizeLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent
        self.name = 'Optimize'
        self.current_algorithm = None
        self.current_control = None

        layout = QGridLayout()

        ''' Algorithm/experiment select layout '''
        self.cost_box = QComboBox()
        self.algorithm_box = QComboBox()
        layout.addWidget(self.algorithm_box, 0, 0)
        layout.addWidget(self.cost_box, 0, 1)
        self.addLayout(layout)

        ''' Pane labels layout '''
        # layout.addWidget(QLabel('Algorithm parameters'), 1, 0)
        # layout.addWidget(QLabel('Experiment parameters'), 1, 1)

        ''' Algorithm parameters '''
        self.apl = QTableWidget()
        layout.addWidget(self.apl, 2, 0)
        self.apl.insertColumn(0)
        self.apl.insertColumn(1)
        self.apl.setHorizontalHeaderLabels(['Parameter', 'Value'])
        self.apl.horizontalHeader().setStretchLastSection(True)

        self.algorithm_params_edit = QTextEdit('')

        ''' Experiment parameters '''
        self.epl = QTableWidget()
        layout.addWidget(self.epl, 2, 1)
        self.epl.insertColumn(0)
        self.epl.insertColumn(1)
        self.epl.setHorizontalHeaderLabels(['Parameter', 'Value'])
        self.epl.horizontalHeader().setStretchLastSection(True)
        self.cost_params_edit = QTextEdit('')


        self.saveLayout = QHBoxLayout()
        self.save_algorithm_button = QPushButton('Save')
        self.save_algorithm_button.clicked.connect(lambda: self.parent.save_params(self, 'algorithm'))
        self.saveLayout.addWidget(self.save_algorithm_button)
        self.save_experiment_button = QPushButton('Save')
        self.save_experiment_button.clicked.connect(lambda: self.parent.save_params(self, 'experiment'))
        self.saveLayout.addWidget(self.save_experiment_button)
        self.addLayout(self.saveLayout)

        plotLayout = QHBoxLayout()
        self.cycles_per_sample_edit = QLineEdit('1')
        self.cycles_per_sample_edit.setMaximumWidth(100)
        plotLayout.addWidget(QLabel('Cycles per sample'))
        plotLayout.addWidget(self.cycles_per_sample_edit)
        self.addLayout(plotLayout)
        self.algorithm_box.currentTextChanged.connect(lambda: self.parent.update_algorithm_and_experiment(self))
        self.cost_box.currentTextChanged.connect(lambda: self.parent.update_algorithm_and_experiment(self))
        optimizeButtonsLayout = QHBoxLayout()
        parent.optimizer_button = QPushButton('Go!')
        parent.optimizer_button.clicked.connect(lambda: parent.start_process(process='optimize', panel = self, settings = {}))

        optimizeButtonsLayout.addWidget(parent.optimizer_button)
        self.addLayout(optimizeButtonsLayout)

    def clear_parameters(self):
        self.apl.setRowCount(0)

    def clear_cost_parameters(self):
        self.epl.setRowCount(0)

    def get_params(self):
        params = {}
        for row in range(self.apl.rowCount()):
            name = self.apl.item(row, 0).text()
            value = self.apl.item(row, 1).text()
            params[name] = float(value)
        return params

    def get_cost_params(self):
        params = {}
        for row in range(self.epl.rowCount()):
            name = self.epl.item(row, 0).text()
            value = self.epl.item(row, 1).text()
            params[name] = float(value)
        return params

    def add_parameter(self, name, value):
        row = self.apl.rowCount()
        self.apl.insertRow(row)
        self.apl.setItem(row, 0, QTableWidgetItem(name))
        self.apl.setItem(row, 1, QTableWidgetItem(str(value)))

    def add_cost_parameter(self, name, value):
        row = self.epl.rowCount()
        self.epl.insertRow(row)
        self.epl.setItem(row, 0, QTableWidgetItem(name))
        self.epl.setItem(row, 1, QTableWidgetItem(str(value)))

    def get_settings_from_gui(self):
        settings = {}
        settings['state'] = self.parent.parent.treeWidget.get_selected_state()
        settings['cost_name'] = self.cost_box.currentText()
        try:
            settings['control'] = self.parent.parent.treeWidget.get_selected_control()
        except IndexError:
            log.warn('Select inputs before starting optimization!')
            return

        settings['algo_params'] = self.get_params()
        settings['cost_params'] = self.get_cost_params()
        settings['callback'] = None
        settings['cost_params']['cycles per sample'] = int(self.cycles_per_sample_edit.text())
        return settings

    def run_process(self, sampler, settings, index, t):
        algo = settings['algorithm']
        state = settings['state']
        cost = settings['cost']
        params = settings['algo_params']
        cost_params = settings['cost_params']
        control = settings['control']
        algo(state, cost, params, cost_params)
        log.info('Optimization complete!')
        control.samplers[index]['status'] = 'Done'
        sampler.log(t.replace(':','') + ' - ' + cost.__name__ + ' - ' + algo.__name__)
        sampler.active = False
