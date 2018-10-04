from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QHBoxLayout, QCheckBox, QTabWidget, QLineEdit)
from PyQt5.QtCore import *
from emergent.archetypes.optimizer import Optimizer
from emergent.archetypes.parallel import ProcessHandler
import inspect
import json
import logging as log
import time
from scipy.stats import linregress
import numpy as np

class OptimizerLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent

        self.addWidget(QLabel('Experiments'))
        self.cost_box = QComboBox()
        self.addWidget(self.cost_box)

        self.tabWidget = QTabWidget()

        ''' Create optimizer tab '''
        self.optimizeTab = QWidget()
        self.optimizeTabLayout = QVBoxLayout()
        self.optimizeTab.setLayout(self.optimizeTabLayout)
        self.tabWidget.addTab(self.optimizeTab, 'Optimize')
        self.addWidget(self.tabWidget)

        self.algorithm_box = QComboBox()
        self.optimizeTabLayout.addWidget(self.algorithm_box)

        self.paramsLayout = QHBoxLayout()

        self.optimizerParamsLayout = QVBoxLayout()
        self.params_edit = QTextEdit('')
        self.optimizerParamsLayout.addWidget(QLabel('Algorithm parameters'))
        self.optimizerParamsLayout.addWidget(self.params_edit)
        self.paramsLayout.addLayout(self.optimizerParamsLayout)

        self.experimentParamsLayout = QVBoxLayout()
        self.cost_params_edit = QTextEdit('')
        self.experimentParamsLayout.addWidget(QLabel('Experiment parameters'))
        self.experimentParamsLayout.addWidget(self.cost_params_edit)
        self.paramsLayout.addLayout(self.experimentParamsLayout)

        self.optimizeTabLayout.addLayout(self.paramsLayout)

        ''' Plot options buttons '''
        plotLayout = QHBoxLayout()
        self.plot_label = QLabel('Plot result')
        self.plot_checkbox = QCheckBox()
        plotLayout.addWidget(self.plot_label)
        plotLayout.addWidget(self.plot_checkbox)
        self.save_label = QLabel('Save plot')
        self.save_checkbox = QCheckBox()
        plotLayout.addWidget(self.save_label)
        plotLayout.addWidget(self.save_checkbox)
        self.optimizeTabLayout.addLayout(plotLayout)

        self.parent.treeWidget.itemSelectionChanged.connect(self.update_algorithm_display)
        self.algorithm_box.currentTextChanged.connect(self.update_algorithm)
        self.cost_box.currentTextChanged.connect(self.update_experiment)

        # self.optimizeProcessingLayout = QHBoxLayout()
        # self.optimizeProcessingLayout.addWidget(QLabel('Operation (n/c)'))
        # self.optimizeProcessingComboBox = QComboBox()
        # for item in ['mean', 'stdev', 'peak-to-peak', 'slope']:
        #     self.optimizeProcessingComboBox.addItem(item)
        # self.optimizeProcessingLayout.addWidget(self.optimizeProcessingComboBox)
        # self.optimizeTabLayout.addLayout(self.optimizeProcessingLayout)

        self.optimizer_button = QPushButton('Go!')
        self.optimizer_button.clicked.connect(self.optimize)
        self.optimizeTabLayout.addWidget(self.optimizer_button)

        self.progress_bar = QProgressBar()
        self.max_progress = 100
        self.progress_bar.setMaximum(self.max_progress)
        self.optimizeTabLayout.addWidget(self.progress_bar)


        ''' Create Run tab '''
        self.runTab = QWidget()
        self.runTabLayout = QVBoxLayout()
        self.runTab.setLayout(self.runTabLayout)
        self.tabWidget.addTab(self.runTab, 'Run')

        self.runIterationsLayout = QHBoxLayout()
        self.runIterationsLayout.addWidget(QLabel('Iterations'))
        self.runIterationsComboBox = QComboBox()
        for power in range(8):
            self.runIterationsComboBox.addItem(str(2**power))
        self.runIterationsLayout.addWidget(self.runIterationsComboBox)
        self.runTabLayout.addLayout(self.runIterationsLayout)

        self.runDelayLayout = QHBoxLayout()
        self.runDelayLayout.addWidget(QLabel('Delay (ms)'))
        self.runDelayEdit = QLineEdit('0')
        self.runDelayLayout.addWidget(self.runDelayEdit)
        self.runTabLayout.addLayout(self.runDelayLayout)

        # self.runProcessingLayout = QHBoxLayout()
        # self.runProcessingLayout.addWidget(QLabel('Operation'))
        # self.runProcessingComboBox = QComboBox()
        # for item in ['mean', 'stdev', 'peak-to-peak', 'slope']:
        #     self.runProcessingComboBox.addItem(item)
        # self.runProcessingLayout.addWidget(self.runProcessingComboBox)
        # self.runTabLayout.addLayout(self.runProcessingLayout)

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

    def update_algorithm_display(self):
        ''' Updates the algorithm box with the methods available to the currently selected control. '''
        tree = self.parent.treeWidget
        control = tree.currentItem().root
        self.algorithm_box.clear()
        for item in control.optimizer.list_algorithms():
            self.algorithm_box.addItem(item.replace('_',' '))
        self.cost_box.clear()
        for item in control.list_costs():
            self.cost_box.addItem(item)
        self.update_algorithm()

    def update_progress_bar(self, progress):
        self.progress_bar.setValue(progress*self.max_progress)
        #self.parent.app.processEvents()
        qApp.processEvents(QEventLoop.ExcludeUserInputEvents)

    def hyperparameter(self):
        control = self.parent.treeWidget.controls['control']
        control.optimizer.grid_optimize(control.state, control.cost_coupled)

    def optimize(self):
        # self._run_thread(self.start_optimizer, stoppable=False)
        self.start_optimizer()

    # def postprocess(self, data, method):
    #     if method == 'mean':
    #         return np.mean(data)
    #     if method == 'stdev':
    #         return np.std(data)
    #     if method == 'slope':
    #         axis = np.linspace(0,1,len(data))
    #         slope, intercept, r, p, err = linregress(axis, data)
    #         return slope
    #     if method == 'peak-to-peak':
    #         return np.ptp(data)

    def run_experiment(self, stopped):
        control = self.parent.treeWidget.get_selected_control()
        experiment = getattr(control, self.cost_box.currentText())
        iterations = int(self.runIterationsComboBox.currentText())
        delay = float(self.runDelayEdit.text())
        # operation = self.runProcessingComboBox.currentText()
        count = 0
        while not stopped() and count < iterations:
            state = control.state
            result = experiment(state)
            # if type(result) is np.ndarray:
                # result = self.postprocess(result, operation)
            self.runResultEdit.setText(str(result))
            qApp.processEvents(QEventLoop.ExcludeUserInputEvents)
            count += 1
            time.sleep(delay/1000)

    def start_experiment(self):
        self._run_thread(self.run_experiment)

    def stop_experiment(self):
        self._quit_thread(self.run_experiment)

    def start_optimizer(self):
        ''' Call chosen optimization routine with user-selected cost function and parameters '''
        algorithm_name = self.algorithm_box.currentText()
        control = self.parent.treeWidget.get_selected_control()
        func = getattr(control.optimizer, algorithm_name.replace(' ','_'))
        params = self.params_edit.toPlainText().replace('\n','').replace("'", '"')
        params = json.loads(params)
        params['plot']=self.plot_checkbox.isChecked()
        params['save']=self.save_checkbox.isChecked()

        cost_params = self.cost_params_edit.toPlainText().replace('\n','').replace("'", '"')
        cost_params = json.loads(cost_params)

        cost_name = self.cost_box.currentText()
        cost = getattr(control, cost_name)
        state = self.parent.treeWidget.get_selected_state()
        if state == {}:
            log.warn('Please select at least one Input node for optimization.')
        else:
            log.info('Started optimization of %s experiment using %s algorithm.'%(cost_name, algorithm_name))
            func(state, cost, params, cost_params, self.update_progress_bar)
            log.info('Optimization complete!')

    def update_algorithm(self):
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
