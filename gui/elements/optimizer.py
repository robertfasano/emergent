from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QHBoxLayout, QCheckBox)
from PyQt5.QtCore import *
from archetypes.optimizer import Optimizer
from archetypes.parallel import ProcessHandler
import inspect
import json
import logging as log

class OptimizerLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent

        self.addWidget(QLabel('Optimizer'))
        self.algorithm_box = QComboBox()
        self.addWidget(self.algorithm_box)
        self.parent.treeWidget.itemSelectionChanged.connect(self.update_algorithm_display)
        self.algorithm_box.currentTextChanged.connect(self.update_algorithm)

        self.params_edit = QTextEdit('')
        self.addWidget(self.params_edit)

        plotLayout = QHBoxLayout()
        self.plot_label = QLabel('Plot result')
        self.plot_checkbox = QCheckBox()
        plotLayout.addWidget(self.plot_label)
        plotLayout.addWidget(self.plot_checkbox)
        self.save_label = QLabel('Save plot')
        self.save_checkbox = QCheckBox()
        plotLayout.addWidget(self.save_label)
        plotLayout.addWidget(self.save_checkbox)

        self.addLayout(plotLayout)

        self.cost_box = QComboBox()
        self.addWidget(self.cost_box)

        self.optimizer_button = QPushButton('Go!')
        self.optimizer_button.clicked.connect(self.optimize)
        self.addWidget(self.optimizer_button)

        self.progress_bar = QProgressBar()
        self.max_progress = 100
        self.progress_bar.setMaximum(self.max_progress)
        self.addWidget(self.progress_bar)

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

    def start_optimizer(self):
        ''' Call chosen optimization routine with user-selected cost function and parameters '''
        control = self.parent.treeWidget.get_selected_control()
        func = getattr(control.optimizer, self.algorithm_box.currentText().replace(' ','_'))
        params = self.params_edit.toPlainText().replace('\n','').replace("'", '"')
        params = json.loads(params)
        params['plot']=self.plot_checkbox.isChecked()
        params['save']=self.save_checkbox.isChecked()

        cost = getattr(control, self.cost_box.currentText())
        state = self.parent.treeWidget.get_selected_state()
        if state == {}:
            log.warn('Please select at least one Input node for optimization.')
        else:
            points, cost = func(state, cost, params, self.update_progress_bar)
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
