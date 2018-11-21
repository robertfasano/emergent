from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QHBoxLayout, QCheckBox, QTabWidget, QLineEdit, QSlider)
from PyQt5.QtCore import *
from emergent.archetypes.optimizer import Optimizer
from emergent.archetypes.sampler import Sampler
from emergent.archetypes.parallel import ProcessHandler
from emergent.utility import list_algorithms, list_triggers
import inspect
import json
import logging as log
import time
from scipy.stats import linregress
import numpy as np
import datetime
import json

class ServoLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent

        self.algorithm_box = QComboBox()
        self.addWidget(self.algorithm_box)

        self.cost_box = QComboBox()
        self.addWidget(self.cost_box)

        self.current_control = None
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
        # self.cost_box.currentTextChanged.connect(self.update_algorithm_and_experiment)
        self.cost_box.currentTextChanged.connect(lambda: self.parent.update_algorithm_and_experiment(self))

        optimizeButtonsLayout = QHBoxLayout()
        self.optimizer_button = QPushButton('Go!')
        self.optimizer_button.clicked.connect(lambda: parent.start_process(process='servo', panel = self, settings = {}))

        optimizeButtonsLayout.addWidget(self.optimizer_button)
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
        return settings

    def start_optimizer(self, func, settings, sampler, index, row, t, algorithm_name):
        func(settings['state'], settings['cost'], settings['algo_params'], settings['cost_params'], callback = settings['callback'])
        log.info('Optimization complete!')
        settings['control'].samplers[index]['status'] = 'Done'
        sampler.log(t.replace(':','') + ' - ' + settings['cost_name'] + ' - ' + algorithm_name)

    def stop_optimizer(self):
        control = self.parent.parent.treeWidget.get_selected_control()
        for d in control.samplers.values():
            d['sampler'].terminate()
