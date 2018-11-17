from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QHBoxLayout, QCheckBox, QTabWidget, QLineEdit, QSlider)
from PyQt5.QtCore import *
from emergent.archetypes.optimizer import Optimizer
from emergent.gui.elements.OptimizeTab import OptimizeTab
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

        self.error_box = QComboBox()
        self.addWidget(self.error_box)

        self.current_control = None
        paramsLayout = QHBoxLayout()
        optimizerParamsLayout = QVBoxLayout()
        self.params_edit = QTextEdit('')
        optimizerParamsLayout.addWidget(QLabel('Algorithm parameters'))
        optimizerParamsLayout.addWidget(self.params_edit)
        paramsLayout.addLayout(optimizerParamsLayout)
        experimentParamsLayout = QVBoxLayout()
        self.error_params_edit = QTextEdit('')
        experimentParamsLayout.addWidget(QLabel('Experiment parameters'))
        experimentParamsLayout.addWidget(self.error_params_edit)
        paramsLayout.addLayout(experimentParamsLayout)
        self.addLayout(paramsLayout)
        self.parent.treeWidget.itemSelectionChanged.connect(self.update_control)
        self.error_box.currentTextChanged.connect(self.update_experiment)
        optimizeButtonsLayout = QHBoxLayout()
        self.optimizer_button = QPushButton('Go!')
        self.optimizer_button.clicked.connect(self.prepare_optimizer)
        optimizeButtonsLayout.addWidget(self.optimizer_button)
        self.addLayout(optimizeButtonsLayout)

    def update_algorithm(self):
        control = self.parent.treeWidget.currentItem().root
        optimizer, index = control.attach_optimizer(None, None)
        f = optimizer.PID
        ''' Read default params dict from source code and insert in self.params_edit. '''
        args = inspect.signature(f).parameters
        args = list(args.items())
        arguments = []
        for a in args:
            name = a[0]
            if name == 'params':
                default = str(a[1])
                if default == name:
                    default = 'Enter'
                else:
                    default = default.split('=')[1]
                    params = json.loads(default.replace("'", '"'))
                    default = json.dumps(self.update_experiment(params))
                    default = default.replace('{', '{\n')
                    default = default.replace(',', ',\n')
                    default = default.replace('}', '\n}')
                    self.params_edit.setText(default)

    def update_algorithm_display(self):
        ''' Updates the algorithm box with the methods available to the currently selected control. '''
        tree = self.parent.treeWidget
        control = tree.currentItem().root
        self.error_box.clear()
        for item in control.list_errors():
            self.error_box.addItem(item)
        self.update_algorithm()

    def update_control(self):
        control = self.parent.treeWidget.currentItem().root
        if control == self.current_control:
            return
        else:
            self.current_control = control
        self.update_algorithm_display()

    def prepare_optimizer(self):
        ''' Call chosen optimization routine with user-selected cost function and parameters '''
        try:
            control = self.parent.treeWidget.get_selected_control()
        except IndexError:
            log.warn('Select inputs before starting optimization!')
            return
        state = self.parent.treeWidget.get_selected_state()
        cost_name = self.error_box.currentText()
        cost = getattr(control, cost_name)
        optimizer, index = control.attach_optimizer(state, cost)
        control.optimizers[index]['status'] = 'Servoing'
        t = datetime.datetime.strftime(datetime.datetime.now(), '%H:%M')
        row = self.parent.historyPanel.add_event(t, cost_name, 'PID', 'Servoing', optimizer)
        func = optimizer.PID
        params = self.params_edit.toPlainText().replace('\n','').replace("'", '"')
        params = json.loads(params)

        error_params = self.error_params_edit.toPlainText().replace('\n','').replace("'", '"')
        error_params = json.loads(error_params)

        if state == {}:
            log.warn('Please select at least one Input node for optimization.')
        else:
            log.info('Started optimization of %s experiment using %s algorithm.'%(cost_name, 'PID'))
            self._run_thread(self.start_optimizer, args=(func, state, cost, params, error_params, control, optimizer, index, row, t, cost_name, 'PID'), stoppable=False)

    def start_optimizer(self, func, state, cost, params, error_params, control, optimizer, index, row, t, cost_name, algorithm_name):
        func(state, cost, params, error_params)
        log.info('Optimization complete!')
        control.optimizers[index]['status'] = 'Done'
        optimizer.log(t.replace(':','') + ' - ' + cost_name + ' - ' + algorithm_name)

    def stop_optimizer(self):
        control = self.parent.treeWidget.get_selected_control()
        for d in control.optimizers.values():
            d['optimizer'].terminate()

    def update_experiment(self, params=None):
        ''' Read default params dict from source code and insert it in self.error_params_edit.
            If a params dict is passed, this will insert any duplicate entries into that dict
            instead of this one - this allows you to save algorithm parameters for each
            experiment separately.'''
        if self.error_box.currentText() is not '':
            try:
                control = self.parent.treeWidget.get_selected_control()
            except IndexError:
                return
            f = getattr(control, self.error_box.currentText())
            args = inspect.signature(f).parameters
            args = list(args.items())
            for a in args:
                name = a[0]
                if name == 'error_params':
                    default = str(a[1])
                    if default == name:
                        default = 'Enter'
                    else:
                        default = default.split('=')[1]

                        if params is not None:
                            exp_params = json.loads(default.replace("'", '"'))
                            params_list = list(exp_params.keys())
                            for param in params_list:
                                if param in params:
                                    params[param] = exp_params[param]
                                    del exp_params[param]
                            default = json.dumps(exp_params)
                        default = default.replace('{', '{\n')
                        default = default.replace(',', ',\n')
                        default = default.replace('}', '\n}')
                        self.error_params_edit.setText(default)
                        return params