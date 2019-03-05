''' The OptimizeTab allows the user to choose algorithms and their parameters and
    launch optimizations. '''
from PyQt5.QtWidgets import (QComboBox, QPushButton, QTabWidget, QVBoxLayout, QWidget,
        QTableWidgetItem, QTableWidget, QHBoxLayout, QGridLayout, QLabel, QMenu, QAction)
from PyQt5.QtCore import *
from PyQt5.QtGui import QCursor
from emergent.modules.parallel import ProcessHandler
import logging as log
import numpy as np
from emergent.gui.elements.ParameterTable import ParameterTable
from emergent.utilities import recommender

class ModelLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent
        self.name = 'Model'

        ''' Experiment select layout '''
        self.experiment_layout = QVBoxLayout()
        label = QLabel('Experiment')
        label.setStyleSheet('color:"#000000"; font-weight: light; font-family: "Exo 2"; font-size: 14px; background-color: transparent')
        self.experiment_layout.addWidget(label)
        self.experiment_box = QComboBox()
        self.experiment_layout.addWidget(self.experiment_box)


        ''' Experiment parameters '''
        self.experiment_table = ParameterTable()

        ''' Model select layout '''
        self.modelLayout = QVBoxLayout()
        self.model_box = QComboBox()
        for item in ['None', 'GaussianProcess', 'NonlinearModel']:
            self.model_box.addItem(item)
        label = QLabel('Model')
        label.setStyleSheet('color:"#000000"; font-weight: light; font-family: "Exo 2"; font-size: 14px; background-color: transparent')
        self.modelLayout.addWidget(label)
        self.modelLayout.addWidget(self.model_box)



        ''' Model parameters '''
        self.model_table = ParameterTable()

        ''' Algorithm select layout '''
        self.sampler_layout = QVBoxLayout()
        label = QLabel('Sampler')
        label.setStyleSheet('color:"#000000"; font-weight: light; font-family: "Exo 2"; font-size: 14px; background-color: transparent')
        self.sampler_layout.addWidget(label)
        self.sampler_box = QComboBox()
        self.sampler_layout.addWidget(self.sampler_box)

        self.sampler_table = ParameterTable()


        ''' Add parameter tables in tabs '''
        self.horizontal_layout = QHBoxLayout()
        self.tab_widget = QTabWidget()
        self.experiment_layout.addWidget(self.experiment_table)
        self.horizontal_layout.addLayout(self.experiment_layout)
        self.modelLayout.addWidget(self.model_table)
        self.horizontal_layout.addLayout(self.modelLayout)

        self.sampler_layout.addWidget(self.sampler_table)
        self.horizontal_layout.addLayout(self.sampler_layout)

        self.addLayout(self.horizontal_layout)

        # self.sampler_box.currentTextChanged.connect(lambda: self.parent.update_algorithm_and_experiment(self, update_experiment=False))
        # self.experiment_box.currentTextChanged.connect(lambda: self.parent.update_algorithm_and_experiment(self))
        self.experiment_box.currentTextChanged.connect(lambda: self.parent.update_experiment(self))
        self.sampler_box.currentTextChanged.connect(lambda: self.parent.update_sampler(self))
        self.model_box.currentTextChanged.connect(lambda: self.parent.update_model(self))

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
        parent.optimizer_button.clicked.connect(lambda: parent.start_process(process='model'))

        optimizeButtonsLayout.addWidget(parent.optimizer_button)
        self.addLayout(optimizeButtonsLayout)

    def get_settings_from_gui(self):
        settings = {'experiment': {}, 'sampler': {}, 'model': {}, 'process': {}}
        settings['state'] = self.parent.dashboard.tree_widget.get_selected_state()
        settings['experiment']['name'] = self.experiment_box.currentText()
        settings['sampler']['name'] = self.sampler_box.currentText()
        try:
            settings['hub'] = self.parent.dashboard.tree_widget.get_selected_hub()
        except Exception as e:
            if e == IndexError:
                log.warn('Select inputs before starting optimization!')
            elif e == KeyError:
                log.warn('Decentralized processes not yet supported.')
            return
        settings['model']['name'] = self.model_box.currentText()
        settings['sampler']['params'] = self.sampler_table.get_params()

        settings['experiment']['params'] = self.experiment_table.get_params()
        settings['model']['params'] = self.model_table.get_params()

        settings['process']['end at'] = self.goto_box.currentText()
        settings['process']['callback'] = None
        settings['process']['type'] = 'model'

        if 'cycles per sample' not in settings['experiment']['params']:
            settings['experiment']['params']['cycles per sample'] = 1

        return settings