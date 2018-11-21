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
        parent.optimizer_button.clicked.connect(self.prepare_optimizer)
        optimizeButtonsLayout.addWidget(parent.optimizer_button)
        self.addLayout(optimizeButtonsLayout)


    def prepare_optimizer(self):
        ''' Call chosen optimization routine with user-selected cost function and parameters '''
        algorithm_name = self.algorithm_box.currentText()
        try:
            control = self.parent.parent.treeWidget.get_selected_control()
        except IndexError:
            log.warn('Select inputs before starting optimization!')
            return
        state = self.parent.parent.treeWidget.get_selected_state()
        cost_name = self.cost_box.currentText()
        cost = getattr(control, cost_name)
        optimizer, index = control.attach_optimizer(state, cost)
        control.optimizers[index]['status'] = 'Optimizing'
        t = datetime.datetime.strftime(datetime.datetime.now(), '%H:%M')
        row = self.parent.parent.historyPanel.add_event(t, cost_name, algorithm_name, 'Optimizing', optimizer)
        func = getattr(optimizer, algorithm_name.replace(' ','_'))
        params = self.algo_params_edit.toPlainText().replace('\n','').replace("'", '"')
        params = '{' + params + '}'
        params = json.loads(params)

        cost_params = self.cost_params_edit.toPlainText().replace('\n',',').replace("'", '"')
        cost_params = '{' + cost_params + '}'
        cost_params = json.loads(cost_params)
        cost_params['cycles per sample'] = int(self.cycles_per_sample_edit.text())

        if state == {}:
            log.warn('Please select at least one Input node for optimization.')
        else:
            log.info('Started optimization of %s experiment using %s algorithm.'%(cost_name, algorithm_name))
            self._run_thread(self.start_optimizer, args=(func, state, cost, params, cost_params, control, optimizer, index, row, t, cost_name, algorithm_name), stoppable=False)

    def start_optimizer(self, func, state, cost, params, cost_params, control, optimizer, index, row, t, cost_name, algorithm_name):
        func(state, cost, params, cost_params)
        log.info('Optimization complete!')
        control.optimizers[index]['status'] = 'Done'
        # self.parent.parent.historyPanel.update_event_status(row, 'Done')
        optimizer.log(t.replace(':','') + ' - ' + cost_name + ' - ' + algorithm_name)

    def stop_optimizer(self):
        control = self.parent.parent.treeWidget.get_selected_control()
        for d in control.optimizers.values():
            d['optimizer'].terminate()
