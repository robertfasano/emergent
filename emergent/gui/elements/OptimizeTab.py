from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QScrollArea, QProgressBar, QTableWidgetItem, QTableWidget, qApp, QHBoxLayout, QCheckBox, QTabWidget, QLineEdit, QSlider, QGridLayout)
from PyQt5.QtCore import *
from emergent.archetypes.parallel import ProcessHandler
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

        layout = QGridLayout()

        ''' Algorithm/experiment select layout '''
        self.cost_box = QComboBox()
        self.algorithm_box = QComboBox()
        layout.addWidget(self.algorithm_box, 0, 0)
        layout.addWidget(self.cost_box, 0, 1)
        self.addLayout(layout)

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

        self.save_algorithm_button = QPushButton('Save')
        self.save_algorithm_button.clicked.connect(lambda: self.parent.save_params(self, 'algorithm'))
        self.save_experiment_button = QPushButton('Save')
        self.save_experiment_button.clicked.connect(lambda: self.parent.save_params(self, 'experiment'))
        layout.addWidget(self.save_algorithm_button, 3, 0)
        layout.addWidget(self.save_experiment_button, 3, 1)

        self.reset_algorithm_button = QPushButton('Reset')
        self.reset_algorithm_button.clicked.connect(lambda: self.parent.update_algorithm_and_experiment(self, default=True, update_experiment=False))
        self.reset_experiment_button = QPushButton('Reset')
        self.reset_experiment_button.clicked.connect(lambda: self.parent.update_algorithm_and_experiment(self, default=True, update_algorithm=False))
        layout.addWidget(self.reset_algorithm_button, 4, 0)
        layout.addWidget(self.reset_experiment_button, 4, 1)


        self.algorithm_box.currentTextChanged.connect(lambda: self.parent.update_algorithm_and_experiment(self))
        self.cost_box.currentTextChanged.connect(lambda: self.parent.update_algorithm_and_experiment(self))
        optimizeButtonsLayout = QHBoxLayout()
        parent.optimizer_button = QPushButton('Go!')
        parent.optimizer_button.clicked.connect(lambda: parent.start_process(process='optimize', panel = self, settings = {}))

        optimizeButtonsLayout.addWidget(parent.optimizer_button)
        self.addLayout(optimizeButtonsLayout)

    def get_settings_from_gui(self):
        settings = {}
        settings['state'] = self.parent.parent.treeWidget.get_selected_state()
        settings['cost_name'] = self.cost_box.currentText()
        try:
            settings['control'] = self.parent.parent.treeWidget.get_selected_control()
        except IndexError:
            log.warn('Select inputs before starting optimization!')
            return

        settings['algo_params'] = self.parent.get_params(self)
        settings['cost_params'] = self.parent.get_cost_params(self)
        settings['callback'] = None
        if 'cycles per sample' not in settings['cost_params']:
            settings['cost_params']['cycles per sample'] = 1
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
