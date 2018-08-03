from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget)
from PyQt5.QtCore import *
from archetypes.Optimizer import Optimizer
import inspect
import json

class OptimizerLayout(QVBoxLayout):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        self.addWidget(QLabel('Optimizer'))
        self.algorithm_box = QComboBox()
        for item in self.parent.control.optimizer.list_algorithms():
            self.algorithm_box.addItem(item)
        self.addWidget(self.algorithm_box)
        self.algorithm_box.currentTextChanged.connect(self.update_algorithm)
        self.params_edit = QTextEdit('')
        self.addWidget(self.params_edit)

        self.cost_box = QComboBox()
        for item in self.parent.control.list_costs():
            self.cost_box.addItem(item)
        self.addWidget(self.cost_box)

        self.optimizer_button = QPushButton('Go!')
        self.optimizer_button.clicked.connect(self.start_optimizer)
        self.addWidget(self.optimizer_button)

        self.update_algorithm()
        ''' Ensure that only Inputs are selectable '''
        for item in self.parent.treeLayout.get_all_items():
            if self.parent.treeLayout.get_layer(item) != 2:
                item.setFlags(Qt.ItemIsEnabled)

    def start_optimizer(self):
        ''' Call chosen optimization routine with user-selected cost function and parameters '''
        func = getattr(self.parent.control.optimizer, self.algorithm_box.currentText())
        params = self.params_edit.toPlainText().replace('\n','').replace("'", '"')
        print(params)
        params = json.loads(params)
        cost = getattr(self.parent.control, self.cost_box.currentText())
        state = self.parent.treeLayout.get_selected_state()
        if state == {}:
            print('Please select at least one Input node for optimization.')
        else:
            points, cost = func(state, cost, params)

    def update_algorithm(self):
        f = getattr(Optimizer, self.algorithm_box.currentText())
        ''' Read default params dict from source code and insert in self.params_edit. '''
        args = inspect.signature(f).parameters
        args = list(args.items())
        arguments = []
        for a in args:
            name = a[0]
            default = str(a[1])
            if default == name:
                default = 'Enter'
            else:
                default = default.split('=')[1]
                default = default.replace('{', '{\n')
                default = default.replace(',', ',\n')
                default = default.replace('}', '\n}')
                self.params_edit.setText(default)