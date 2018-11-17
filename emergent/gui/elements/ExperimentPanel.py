from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QHBoxLayout, QCheckBox, QTabWidget, QLineEdit, QSlider)
from PyQt5.QtCore import *
from emergent.archetypes.optimizer import Optimizer
from emergent.gui.elements.OptimizeTab import OptimizeTab
from emergent.archetypes.parallel import ProcessHandler
from emergent.gui.elements.ServoPanel import ServoLayout
from emergent.utility import list_algorithms, list_triggers
import inspect
import json
import logging as log
import time
from scipy.stats import linregress
import numpy as np
import datetime

class OptimizerLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent

        self.cost_box = QComboBox()

        self.tabWidget = QTabWidget()
        self.addWidget(self.tabWidget)

        self.current_algorithm = None
        self.current_control = None

        ''' Create Optimizer tab '''
        optimizeTab = OptimizeTab(parent=self)
        self.tabWidget.addTab(optimizeTab, 'Optimize')

        ''' Create Servo tab '''
        servoTab = QWidget()
        self.servoPanel = ServoLayout(self.parent)
        servoTab.setLayout(self.servoPanel)
        self.tabWidget.addTab(servoTab, 'Servo')

        ''' Create Run tab '''
        self.runTab = QWidget()
        self.runTabLayout = QVBoxLayout()
        self.runTabLayout.addWidget(self.cost_box)

        self.runTab.setLayout(self.runTabLayout)
        self.tabWidget.addTab(self.runTab, 'Run')
        self.runIterationsLayout = QHBoxLayout()
        self.run_experimentParamsLayout = QVBoxLayout()
        self.run_cost_params_edit = QTextEdit('')
        self.run_experimentParamsLayout.addWidget(QLabel('Experiment parameters'))
        self.run_experimentParamsLayout.addWidget(self.run_cost_params_edit)
        self.runTabLayout.addLayout(self.run_experimentParamsLayout)
        self.runIterationsLayout.addWidget(QLabel('Iterations'))
        self.runIterationsSlider = QSlider(Qt.Horizontal)
        self.runIterationsSlider.valueChanged.connect(self.updateIterations)
        self.runIterationsSlider.setRange(1,8)
        self.runIterationsSlider.setSingleStep(1)
        self.runIterationsLayout.addWidget(self.runIterationsSlider)
        self.runIterationsEdit = QLineEdit('')
        self.runIterationsLayout.addWidget(self.runIterationsEdit)
        self.runIterationsSlider.setValue(8)
        self.runTabLayout.addLayout(self.runIterationsLayout)
        self.runDelayLayout = QHBoxLayout()
        self.runDelayLayout.addWidget(QLabel('Delay (ms)'))
        self.runDelayEdit = QLineEdit('0')
        self.runDelayLayout.addWidget(self.runDelayEdit)
        self.trigger_box = QComboBox()
        self.runDelayLayout.addWidget(QLabel('Trigger'))
        self.runDelayLayout.addWidget(self.trigger_box)
        self.runTabLayout.addLayout(self.runDelayLayout)
        self.runButtonsLayout = QHBoxLayout()
        self.runExperimentButton = QPushButton('Run')
        self.runExperimentButton.clicked.connect(self.start_experiment)
        self.runButtonsLayout.addWidget(self.runExperimentButton)
        self.stopExperimentButton = QPushButton('Stop')
        self.stopExperimentButton.clicked.connect(self.stop_experiment)
        self.runButtonsLayout.addWidget(self.stopExperimentButton)
        self.runTabLayout.addLayout(self.runButtonsLayout)
        self.runResultLayout = QHBoxLayout()
        self.runResultLayout.addWidget(QLabel('Result'))
        self.runResultEdit = QLineEdit('')
        self.runResultLayout.addWidget(self.runResultEdit)
        self.runTabLayout.addLayout(self.runResultLayout)

    def updateIterations(self):
        try:
            val = self.runIterationsSlider.value()
            text = {}
            for i in range(1,8):
                text[i] = str(2**i)
            text[8] = 'Continuous'
            self.runIterationsEdit.setText(text[val])
        except AttributeError:
            return

    def update_algorithm_display(self):
        ''' Updates the algorithm box with the methods available to the currently selected control. '''
        tree = self.parent.treeWidget
        control = tree.currentItem().root
        self.algorithm_box.clear()
        for item in list_algorithms():
            self.algorithm_box.addItem(item.replace('_',' '))
        self.cost_box.clear()
        for item in control.list_costs():
            self.cost_box.addItem(item)
        self.update_algorithm()

    def update_control(self):
        control = self.parent.treeWidget.currentItem().root
        if control == self.current_control:
            return
        else:
            self.current_control = control
        self.update_trigger()
        self.update_algorithm_display()

    def update_trigger(self):
        ''' Updates the trigger box with the methods available to the currently selected control. '''
        tree = self.parent.treeWidget
        control = tree.currentItem().root
        self.trigger_box.clear()
        self.trigger_box.addItem('None')
        for item in list_triggers(control):
            self.trigger_box.addItem(item.replace('_',' '))

    def run_experiment(self, stopped):
        control = self.parent.treeWidget.get_selected_control()
        experiment = getattr(control, self.cost_box.currentText())
        trigger = self.trigger_box.currentText()
        if trigger != 'None':
            trigger = getattr(control, trigger)
        iterations = self.runIterationsEdit.text()
        if iterations != 'Continuous':
            iterations = int(iterations)
        delay = float(self.runDelayEdit.text())
        # operation = self.runProcessingComboBox.currentText()
        count = 0
        cost_params = self.run_cost_params_edit.toPlainText().replace('\n','').replace("'", '"')
        cost_params = json.loads(cost_params)
        cost_params['cycles per sample'] = int(self.cycles_per_sample_edit.text())
        if trigger != 'None':
            trigger()
        while not stopped():
            state = control.state
            result = experiment(state, params=cost_params)
            self.runResultEdit.setText(str(result))
            qApp.processEvents(QEventLoop.ExcludeUserInputEvents)
            count += 1
            time.sleep(delay/1000)
            if type(iterations) is int:
                if count >= iterations:
                    break

    def start_experiment(self):
        self._run_thread(self.run_experiment)

    def stop_experiment(self):
        self._quit_thread(self.run_experiment)

    def prepare_optimizer(self):
        ''' Call chosen optimization routine with user-selected cost function and parameters '''
        algorithm_name = self.algorithm_box.currentText()
        try:
            control = self.parent.treeWidget.get_selected_control()
        except IndexError:
            log.warn('Select inputs before starting optimization!')
            return
        state = self.parent.treeWidget.get_selected_state()
        cost_name = self.cost_box.currentText()
        cost = getattr(control, cost_name)
        optimizer, index = control.attach_optimizer(state, cost)
        control.optimizers[index]['status'] = 'Optimizing'
        t = datetime.datetime.strftime(datetime.datetime.now(), '%H:%M')
        row = self.parent.historyPanel.add_event(t, cost_name, algorithm_name, 'Optimizing', optimizer)
        func = getattr(optimizer, algorithm_name.replace(' ','_'))
        params = self.params_edit.toPlainText().replace('\n','').replace("'", '"')
        params = json.loads(params)

        cost_params = self.cost_params_edit.toPlainText().replace('\n','').replace("'", '"')
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
        # self.parent.historyPanel.update_event_status(row, 'Done')
        optimizer.log(t.replace(':','') + ' - ' + cost_name + ' - ' + algorithm_name)

    def stop_optimizer(self):
        control = self.parent.treeWidget.get_selected_control()
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
                        default = default.replace('{', '{\n')
                        default = default.replace(',', ',\n')
                        default = default.replace('}', '\n}')
                        self.params_edit.setText(default)

    def update_experiment(self):
        ''' Read default params dict from source code and insert it in self.cost_params_edit. '''
        if self.cost_box.currentText() is not '':
            try:
                control = self.parent.treeWidget.get_selected_control()
            except IndexError:
                return
            f = getattr(control, self.cost_box.currentText())
            args = inspect.signature(f).parameters
            args = list(args.items())
            for a in args:
                name = a[0]
                if name == 'params':
                    default = str(a[1])
                    if default == name:
                        default = 'Enter'
                    else:
                        default = default.split('=')[1]
                        default = default.replace('{', '{\n')
                        default = default.replace(',', ',\n')
                        default = default.replace('}', '\n}')
                        self.cost_params_edit.setText(default)
                        self.run_cost_params_edit.setText(default)
