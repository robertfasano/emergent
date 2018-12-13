from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QTableWidgetItem, QTableWidget, QHBoxLayout, QGridLayout, QMenu, QAction)
from PyQt5.QtCore import *
from PyQt5.QtGui import QCursor
from emergent.archetypes.parallel import ProcessHandler
import inspect
import datetime
import json
import logging as log
import numpy as np
from emergent.gui.elements.ParameterTable import ParameterTable

class CustomTable(QTableWidget, ProcessHandler):
    def __init__(self, parent):
        QTableWidget.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent

    def contextMenuEvent(self, event):
        self.menu = QMenu(self)
        self.action = QAction('Tune')
        self.action.triggered.connect(lambda: self._run_thread(self.tune))
        self.menu.addAction(self.action)
        self.menu.popup(QCursor.pos())

    def tune(self, stopped):
        pos = self.viewport().mapFromGlobal(QCursor.pos())
        row = self.rowAt(pos.y())
        name = self.item(row, 0).text()
        settings = self.parent.get_settings_from_gui()
        cost = getattr(settings['control'], settings['cost_name'])
        sampler, index = settings['control'].attach_sampler(settings['state'], cost)
        algorithm_name = self.parent.algorithm_box.currentText()
        algorithm = self.parent.parent.get_algorithm(algorithm_name, self.parent)
        algorithm.sampler = sampler
        algorithm.parent = settings['control']
        run = algorithm.run
        default_params = algorithm.params
        min = default_params[name].min
        max = default_params[name].max
        values = np.linspace(min, max, 3)

        c = []
        for v in values:
            if stopped():
                return
            print('Running optimization with %s=%f...'%(name, v))
            settings['algo_params'][name] = v
            algorithm.set_params(settings['algo_params'])
            settings['control'].actuate(settings['state'])
            run(settings['state'])
            c.append(algorithm.sampler.history['cost'].iloc[-1])
            print('...result:', c[-1])

        print(c)


        # state = {'deviceA': {'X': 0, 'Y': 0}}
        # cost_params = {"x0": 0.3,
        #                "noise": 0.01,
        #                "y0": 0.6,
        #                "sigma_y": 0.8,
        #                "theta": 0,
        #                "sigma_x": 0.3,
        #                "cycles per sample": 1}
        # cost = self.sampler.parent.cost_uncoupled
        # algorithm = self.adam
        # params={'learning rate':0.1, 'steps': 100, 'dither': 0.01, 'beta_1': 0.9, 'beta_2': 0.999, 'epsilon': 1e-8}
        # pmin = 0.001
        # pmax = 0.1
        # steps = 10
        # loss = []
        # for p in np.logspace(pmin, pmax, steps):
        #     params['dither'] = p
        #     algorithm(state, cost, params, cost_params)
        #     loss.append(self.sampler.history['cost'].iloc[-1])
        #     print(loss)
        # return loss

class OptimizeLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent
        self.name = 'Optimize'

        layout = QGridLayout()

        ''' Algorithm/experiment select layout '''
        self.cost_box = QComboBox()
        self.algorithm_box = QComboBox()
        layout.addWidget(self.algorithm_box, 0, 0)
        layout.addWidget(self.cost_box, 0, 1)
        self.addLayout(layout)

        ''' Algorithm parameters '''
        self.apl = ParameterTable()
        layout.addWidget(self.apl, 2, 0)
        self.apl.insertColumn(0)
        self.apl.insertColumn(1)
        self.apl.setHorizontalHeaderLabels(['Parameter', 'Value'])
        self.apl.horizontalHeader().setStretchLastSection(True)

        self.algorithm_params_edit = QTextEdit('')

        ''' Experiment parameters '''
        self.epl = ParameterTable()
        layout.addWidget(self.epl, 2, 1)
        self.epl.insertColumn(0)
        self.epl.insertColumn(1)
        self.epl.setHorizontalHeaderLabels(['Parameter', 'Value'])
        self.epl.horizontalHeader().setStretchLastSection(True)
        self.cost_params_edit = QTextEdit('')

        self.save_algorithm_button = QPushButton('Save')
        self.save_algorithm_button.clicked.connect(lambda: self.parent.save_params(self, 'algorithm'))
        self.save_experiment_button = QPushButton('Save')
        self.save_experiment_button.clicked.connect(lambda: self.parent.save_params(self, 'experiment'))
        layout.addWidget(self.save_algorithm_button, 3, 0)
        layout.addWidget(self.save_experiment_button, 3, 1)

        self.reset_algorithm_button = QPushButton('Reset')
        self.reset_algorithm_button.clicked.connect(lambda: self.parent.update_algorithm_and_experiment(self, default=True, update_experiment=False))
        self.reset_experiment_button = QPushButton('Reset')
        self.reset_experiment_button.clicked.connect(lambda: self.parent.update_algorithm_and_experiment(self, default=True, update_algorithm=False))
        layout.addWidget(self.reset_algorithm_button, 4, 0)
        layout.addWidget(self.reset_experiment_button, 4, 1)

        self.algorithm_box.currentTextChanged.connect(lambda: self.parent.update_algorithm_and_experiment(self))
        self.cost_box.currentTextChanged.connect(lambda: self.parent.update_algorithm_and_experiment(self))
        optimizeButtonsLayout = QHBoxLayout()
        parent.optimizer_button = QPushButton('Go!')
        parent.optimizer_button.clicked.connect(lambda: parent.start_process(process='optimize', panel = self, settings = {}))

        optimizeButtonsLayout.addWidget(parent.optimizer_button)
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

        settings['algo_params'] = self.apl.get_params()
        settings['cost_params'] = self.epl.get_params()
        settings['callback'] = None
        if 'cycles per sample' not in settings['cost_params']:
            settings['cost_params']['cycles per sample'] = 1
        return settings

    def run_process(self, sampler, settings, index, t):
        algo = settings['algorithm']
        state = settings['state']
        cost = settings['cost']
        params = settings['algo_params']
        cost_params = settings['cost_params']
        control = settings['control']
        algo(state)
        log.info('Optimization complete!')
        control.samplers[index]['status'] = 'Done'
        sampler.log(t.replace(':','') + ' - ' + cost.__name__ + ' - ' + algo.__name__)
        sampler.active = False

    def openMenu(self, pos):
        item = self.itemAt(pos)
        print(item)
        # globalPos = self.mapToGlobal(pos)
        # menu = QMenu()
        # actions = {}
        # for option in item.node.options:
        #     actions[option] = QAction(option, self)
        #     func = item.node.options[option]
        #     actions[option].triggered.connect(func)
        #     menu.addAction(actions[option])
        #
        # selectedItem = menu.exec_(globalPos)
