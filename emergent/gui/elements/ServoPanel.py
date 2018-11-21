from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QHBoxLayout, QCheckBox, QTabWidget, QLineEdit, QSlider)
from PyQt5.QtCore import *
from emergent.archetypes.optimizer import Optimizer
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
        self.optimizer_button.clicked.connect(self.prepare_optimizer)
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

        settings['params'] = json.loads(params)
        error_params = self.cost_params_edit.toPlainText().replace('\n',',').replace("'", '"')
        error_params = '{' + error_params + '}'
        settings['error_params'] = json.loads(error_params)
        settings['callback'] = None
        return settings

    def prepare_optimizer(self, *args, settings = {'callback': None, 'control':None, 'state':None, 'cost_name': None, 'params': None, 'error_params': None}):
        ''' Call chosen optimization routine with user-selected cost function and parameters '''

        ''' Load any non-passed settings from the GUI '''
        gui_settings = self.get_settings_from_gui()
        print(settings)
        for s in settings:
            if settings[s] is None:
                settings[s] = gui_settings[s]

        settings['cost'] = getattr(settings['control'], settings['cost_name'])
        optimizer, index = settings['control'].attach_optimizer(settings['state'], settings['cost'])
        settings['control'].optimizers[index]['status'] = 'Servoing'
        t = datetime.datetime.strftime(datetime.datetime.now(), '%H:%M')
        row = self.parent.parent.historyPanel.add_event(t, settings['cost_name'], 'PID', 'Servoing', optimizer)
        func = optimizer.PID

        if settings['state'] == {}:
            log.warn('Please select at least one Input node for optimization.')
        else:
            log.info('Started optimization of %s experiment using %s algorithm.'%(settings['cost_name'], 'PID'))
            self._run_thread(self.start_optimizer, args=(func, settings, optimizer, index, row, t, 'PID'), stoppable=False)

    def start_optimizer(self, func, settings, optimizer, index, row, t, algorithm_name):
        func(settings['state'], settings['cost'], settings['params'], settings['error_params'], callback = settings['callback'])
        log.info('Optimization complete!')
        settings['control'].optimizers[index]['status'] = 'Done'
        optimizer.log(t.replace(':','') + ' - ' + settings['cost_name'] + ' - ' + algorithm_name)

    def stop_optimizer(self):
        control = self.parent.parent.treeWidget.get_selected_control()
        for d in control.optimizers.values():
            d['optimizer'].terminate()
