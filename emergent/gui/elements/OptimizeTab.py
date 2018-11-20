from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QHBoxLayout, QCheckBox, QTabWidget, QLineEdit, QSlider)
from PyQt5.QtCore import *
from emergent.archetypes.parallel import ProcessHandler
from emergent.archetypes.optimizer import Optimizer
from emergent.utility import list_algorithms
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

        self.addWidget(parent.cost_box)
        self.algorithm_box = QComboBox()
        self.addWidget(self.algorithm_box)
        paramsLayout = QHBoxLayout()
        optimizerParamsLayout = QVBoxLayout()
        self.params_edit = QTextEdit('')
        optimizerParamsLayout.addWidget(QLabel('Algorithm parameters'))
        optimizerParamsLayout.addWidget(self.params_edit)
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
        parent.parent.treeWidget.itemSelectionChanged.connect(self.update_control)
        self.algorithm_box.currentTextChanged.connect(self.update_algorithm)
        parent.cost_box.currentTextChanged.connect(self.update_experiment)
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
        cost_name = self.parent.cost_box.currentText()
        cost = getattr(control, cost_name)
        optimizer, index = control.attach_optimizer(state, cost)
        control.optimizers[index]['status'] = 'Optimizing'
        t = datetime.datetime.strftime(datetime.datetime.now(), '%H:%M')
        row = self.parent.parent.historyPanel.add_event(t, cost_name, algorithm_name, 'Optimizing', optimizer)
        func = getattr(optimizer, algorithm_name.replace(' ','_'))
        params = self.params_edit.toPlainText().replace('\n','').replace("'", '"')
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


    def update_algorithm(self):
        algo = self.algorithm_box.currentText()
        if algo == self.current_algorithm or algo is '':
            return
        else:
            self.current_algorithm = algo
        if self.algorithm_box.currentText() is not '':
            f = getattr(Optimizer, self.algorithm_box.currentText().replace(' ','_'))
            ''' Read default params dict from source code and insert in self.params_edit. '''
            self.parent.docstring_to_edit(f, self.params_edit)



    def update_algorithm_display(self):
        ''' Updates the algorithm box with the methods available to the currently selected control. '''
        tree = self.parent.parent.treeWidget
        control = tree.currentItem().root
        self.algorithm_box.clear()
        for item in list_algorithms():
            self.algorithm_box.addItem(item.replace('_',' '))
        self.parent.cost_box.clear()
        for item in control.list_costs():
            self.parent.cost_box.addItem(item)
        self.update_algorithm()

    def update_control(self):
        control = self.parent.parent.treeWidget.currentItem().root
        if control == self.current_control:
            return
        else:
            self.current_control = control
        self.update_algorithm_display()

    def update_experiment(self):
        ''' Read default params dict from source code and insert it in self.cost_params_edit. '''
        if self.parent.cost_box.currentText() is not '':
            try:
                control = self.parent.parent.treeWidget.get_selected_control()
            except IndexError:
                return
            f = getattr(control, self.parent.cost_box.currentText())
            self.parent.docstring_to_edit(f, self.cost_params_edit)
