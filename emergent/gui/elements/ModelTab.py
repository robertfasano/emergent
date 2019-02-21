''' The OptimizeTab allows the user to choose algorithms and their parameters and
    launch optimizations. '''
from PyQt5.QtWidgets import (QComboBox, QPushButton, QVBoxLayout,
        QTableWidgetItem, QTableWidget, QHBoxLayout, QGridLayout, QLabel, QMenu, QAction)
from PyQt5.QtCore import *
from PyQt5.QtGui import QCursor
from emergent.modules.parallel import ProcessHandler
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
        cost = getattr(settings['hub'], settings['experiment_name'])
        sampler, index = settings['hub'].attach_sampler(settings['state'], cost)
        algorithm_name = self.parent.sampler_box.currentText()
        algorithm = self.parent.parent.get_algorithm(algorithm_name, self.parent)
        algorithm.sampler = sampler
        algorithm.parent = settings['hub']
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
            settings['algorithm_params'][name] = v
            algorithm.set_params(settings['algorithm_params'])
            settings['hub'].actuate(settings['state'])
            run(settings['state'])
            c.append(algorithm.sampler.history['cost'].iloc[-1])
            print('...result:', c[-1])

        print(c)


        # state = {'thingA': {'X': 0, 'Y': 0}}
        # cost_params = {"x0": 0.3,
        #                "noise": 0.01,
        #                "y0": 0.6,
        #                "sigma_y": 0.8,
        #                "theta": 0,
        #                "sigma_x": 0.3,
        #                "cycles per sample": 1}
        # cost = self.sampler.hub.cost_uncoupled
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

class ModelLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent
        self.name = 'Model'

        ''' Experiment select layout '''
        self.experiment_layout = QHBoxLayout()
        label = QLabel('Experiment')
        label.setStyleSheet('color:"#000000"; font-weight: light; font-family: "Exo 2"; font-size: 14px; background-color: transparent')
        self.experiment_layout.addWidget(label)
        self.experiment_box = QComboBox()
        self.experiment_layout.addWidget(self.experiment_box)
        button = QPushButton('Show/hide parameters')
        button.clicked.connect(lambda: self.show_parameters('experiment'))
        self.experiment_layout.addWidget(button)
        self.addLayout(self.experiment_layout)

        ''' Experiment parameters '''
        self.experiment_table_layout = QHBoxLayout()
        self.experiment_table = ParameterTable()
        self.experiment_table_layout.addWidget(self.experiment_table)
        self.experiment_table.hide()
        self.addLayout(self.experiment_table_layout)

        ''' Model select layout '''
        self.modelLayout = QHBoxLayout()
        self.model_box = QComboBox()
        for item in ['None', 'GaussianProcess', 'NonlinearModel']:
            self.model_box.addItem(item)
        label = QLabel('Model')
        label.setStyleSheet('color:"#000000"; font-weight: light; font-family: "Exo 2"; font-size: 14px; background-color: transparent')
        self.modelLayout.addWidget(label)
        self.modelLayout.addWidget(self.model_box)

        button = QPushButton('Show/hide parameters')
        button.clicked.connect(lambda: self.show_parameters('model'))
        self.modelLayout.addWidget(button)
        self.addLayout(self.modelLayout)

        ''' Model parameters '''
        self.model_table_layout = QHBoxLayout()
        self.model_table = ParameterTable()
        self.model_table_layout.addWidget(self.model_table)
        self.addLayout(self.model_table_layout)

        ''' Algorithm select layout '''
        self.sampler_layout = QHBoxLayout()
        label = QLabel('Sampler')
        label.setStyleSheet('color:"#000000"; font-weight: light; font-family: "Exo 2"; font-size: 14px; background-color: transparent')
        self.sampler_layout.addWidget(label)
        self.sampler_box = QComboBox()
        self.sampler_layout.addWidget(self.sampler_box)
        button = QPushButton('Show/hide parameters')
        button.clicked.connect(lambda: self.show_parameters('sampler'))
        self.sampler_layout.addWidget(button)
        self.addLayout(self.sampler_layout)

        ''' Algorithm parameters '''
        self.sampler_table_layout = QHBoxLayout()
        self.algorithm_table = ParameterTable()
        self.sampler_table_layout.addWidget(self.algorithm_table)
        self.algorithm_table.hide()
        self.addLayout(self.sampler_table_layout)


        self.sampler_box.currentTextChanged.connect(lambda: self.parent.update_algorithm_and_experiment(self, update_experiment=False))
        self.experiment_box.currentTextChanged.connect(lambda: self.parent.update_algorithm_and_experiment(self))

        self.gotoLayout = QHBoxLayout()
        label = QLabel('End at')
        self.gotoLayout.addWidget(label)
        label.setStyleSheet('color:"#000000"; font-weight: light; font-family: "Exo 2"; font-size: 14px; background-color: transparent')
        self.goto_box = QComboBox()
        for item in ['First point', 'Best point', 'Last point']:
            self.goto_box.addItem(item)
        self.gotoLayout.addWidget(self.goto_box)
        self.addLayout(self.gotoLayout)

        self.triggerLayout = QHBoxLayout()
        label = QLabel('Trigger')
        self.triggerLayout.addWidget(label)
        label.setStyleSheet('color:"#000000"; font-weight: light; font-family: "Exo 2"; font-size: 14px; background-color: transparent')
        self.trigger_box = QComboBox()
        self.triggerLayout.addWidget(self.trigger_box)
        self.addLayout(self.triggerLayout)


        optimizeButtonsLayout = QHBoxLayout()
        parent.optimizer_button = QPushButton('Go!')
        parent.optimizer_button.clicked.connect(lambda: parent.start_process(process='model', settings = {}, load_from_gui=True))

        optimizeButtonsLayout.addWidget(parent.optimizer_button)
        self.addLayout(optimizeButtonsLayout)


    def show_parameters(self, name):
        if name == 'model':
            table = self.model_table
            others = [self.experiment_table, self.algorithm_table]
        elif name == 'sampler':
            table = self.algorithm_table
            others = [self.experiment_table, self.model_table]
        else:
            table = self.experiment_table
            others = [self.model_table, self.algorithm_table]
        isVisible = int(table.isVisible())
        table.setVisible(isVisible-1)
        if not isVisible:
            for t in others:
                t.setVisible(isVisible)

    def get_settings_from_gui(self):
        settings = {}
        settings['state'] = self.parent.parent.tree_widget.get_selected_state()
        settings['experiment_name'] = self.experiment_box.currentText()
        settings['algorithm_name'] = self.sampler_box.currentText()
        try:
            settings['hub'] = self.parent.parent.tree_widget.get_selected_hub()
        except Exception as e:
            if e == IndexError:
                log.warn('Select inputs before starting optimization!')
            elif e == KeyError:
                log.warn('Decentralized processes not yet supported.')
            return
        settings['model_name'] = self.model_box.currentText()
        settings['algorithm_params'] = self.algorithm_table.get_params()
        settings['experiment_params'] = self.experiment_table.get_params()
        settings['model_params'] = self.model_table.get_params()
        settings['end at'] = self.goto_box.currentText()
        settings['callback'] = None
        if 'cycles per sample' not in settings['experiment_params']:
            settings['experiment_params']['cycles per sample'] = 1
        return settings

    def run_process(self, sampler):
        sampler.hub.enable_watchdogs(False)
        sampler.algorithm.run(sampler.state)
        sampler.hub.enable_watchdogs(True)
        log.info('Optimization complete!')
        sampler.log(sampler.start_time.replace(':','') + ' - ' + sampler.experiment.__name__ + ' - ' + sampler.algorithm.name)
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
