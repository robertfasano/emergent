from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp)
from PyQt5.QtCore import *
from archetypes.optimizer import Optimizer
from archetypes.parallel import ProcessHandler
import inspect
import json

class OptimizerLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent

        self.addWidget(QLabel('Optimizer'))
        self.algorithm_box = QComboBox()
        for control in self.parent.controls.values():
            for item in control.optimizer.list_algorithms():
                self.algorithm_box.addItem(item)
        self.addWidget(self.algorithm_box)
        self.algorithm_box.currentTextChanged.connect(self.update_algorithm)
        self.params_edit = QTextEdit('')
        self.addWidget(self.params_edit)

        self.cost_box = QComboBox()
        for control in self.parent.controls.values():
            for item in control.list_costs():
                self.cost_box.addItem(item)
        self.addWidget(self.cost_box)

        self.optimizer_button = QPushButton('Go!')
        self.optimizer_button.clicked.connect(self.optimize)
        self.addWidget(self.optimizer_button)

        self.progress_bar = QProgressBar()
        self.max_progress = 100
        self.progress_bar.setMaximum(self.max_progress)
        self.addWidget(self.progress_bar)

        self.update_algorithm()
        ''' Ensure that only Inputs are selectable '''
        for item in self.parent.treeLayout.get_all_items():
            if item.level != 2:
                item.setFlags(Qt.ItemIsEnabled)

    def update_progress_bar(self, progress):
        self.progress_bar.setValue(progress*self.max_progress)
        #self.parent.app.processEvents()
        qApp.processEvents(QEventLoop.ExcludeUserInputEvents)

    def hyperparameter(self):
        control = self.parent.treeLayout.controls['control']
        control.optimizer.grid_optimize(control.state, control.cost_coupled)
    def optimize(self):
        # self._run_thread(self.start_optimizer, stoppable=False)
        self.start_optimizer()

    def start_optimizer(self):
        ''' Call chosen optimization routine with user-selected cost function and parameters '''
        control = self.parent.treeLayout.get_selected_control()
        func = getattr(control.optimizer, self.algorithm_box.currentText())
        params = self.params_edit.toPlainText().replace('\n','').replace("'", '"')
        params = json.loads(params)
        cost = getattr(control, self.cost_box.currentText())
        state = self.parent.treeLayout.get_selected_state()
        if state == {}:
            print('Please select at least one Input node for optimization.')
        else:
            points, cost = func(state, cost, params, self.update_progress_bar)
            print('Optimization complete!')
            self.parent.treeLayout.update_state(control.name)

    def update_algorithm(self):
        f = getattr(Optimizer, self.algorithm_box.currentText())
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
