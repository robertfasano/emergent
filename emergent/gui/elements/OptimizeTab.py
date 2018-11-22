from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QHBoxLayout, QCheckBox, QTabWidget, QLineEdit, QSlider)
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
        self.current_algorithm = None
        self.current_control = None
        self.cost_box = QComboBox()

        self.addWidget(self.cost_box)

        self.algorithm_box = QComboBox()
        self.addWidget(self.algorithm_box)
        paramsLayout = QHBoxLayout()
        optimizerParamsLayout = QVBoxLayout()
        self.algo_params_edit = QTextEdit('')
        optimizerParamsLayout.addWidget(QLabel('Algorithm parameters'))
        optimizerParamsLayout.addWidget(self.algo_params_edit)
        paramsLayout.addLayout(optimizerParamsLayout)
        experimentParamsLayout = QVBoxLayout()
        self.cost_params_edit = QTextEdit('')
        experimentParamsLayout.addWidget(QLabel('Experiment parameters'))
        experimentParamsLayout.addWidget(self.cost_params_edit)
        paramsLayout.addLayout(experimentParamsLayout)
        self.addLayout(paramsLayout)
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

    def get_settings_from_gui(self):
        settings = {}
        settings['state'] = self.parent.parent.treeWidget.get_selected_state()
        settings['cost_name'] = self.cost_box.currentText()
        try:
            settings['control'] = self.parent.parent.treeWidget.get_selected_control()
        except IndexError:
            log.warn('Select inputs before starting optimization!')
            return
        params = self.algo_params_edit.toPlainText().replace('\n',',').replace("'", '"')
        params = '{' + params + '}'

        settings['algo_params'] = json.loads(params)
        error_params = self.cost_params_edit.toPlainText().replace('\n',',').replace("'", '"')
        error_params = '{' + error_params + '}'
        settings['cost_params'] = json.loads(error_params)
        settings['callback'] = None
        settings['cost_params']['cycles per sample'] = int(self.cycles_per_sample_edit.text())
        return settings

    def run_process(self, sampler, settings, index, t):
        algo = settings['algo']
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
