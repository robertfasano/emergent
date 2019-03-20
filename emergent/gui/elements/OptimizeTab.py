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

class OptimizeLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent
        self.name = 'Optimize'

        layout = QGridLayout()

        ''' Algorithm/experiment select layout '''
        self.experiment_box = QComboBox()
        self.algorithm_box = QComboBox()
        layout.addWidget(self.algorithm_box, 0, 0)
        layout.addWidget(self.experiment_box, 0, 1)
        self.addLayout(layout)

        ''' Algorithm parameters '''
        self.algorithm_table = ParameterTable()
        layout.addWidget(self.algorithm_table, 2, 0)

        ''' Experiment parameters '''
        self.experiment_table = ParameterTable()
        layout.addWidget(self.experiment_table, 2, 1)

        self.algorithm_box.currentTextChanged.connect(lambda: self.parent.update_algorithm_and_experiment(self, update_experiment=False))
        self.experiment_box.currentTextChanged.connect(lambda: self.parent.update_algorithm_and_experiment(self))

        self.triggerLayout = QHBoxLayout()
        label = QLabel('Trigger')
        self.triggerLayout.addWidget(label)
        label.setStyleSheet('color:"#000000"; font-weight: light; font-family: "Exo 2"; font-size: 14px; background-color: transparent')
        self.trigger_box = QComboBox()
        self.triggerLayout.addWidget(self.trigger_box)
        self.addLayout(self.triggerLayout)


        optimizeButtonsLayout = QHBoxLayout()
        parent.optimizer_button = QPushButton('Go!')
        parent.optimizer_button.clicked.connect(lambda: parent.start_process(process='optimize', settings = {}, load_from_gui=True))

        optimizeButtonsLayout.addWidget(parent.optimizer_button)
        self.addLayout(optimizeButtonsLayout)


    def get_settings_from_gui(self):
        settings = {}
        settings['state'] = self.parent.parent.tree_widget.get_selected_state()
        settings['experiment_name'] = self.experiment_box.currentText()
        settings['algorithm_name'] = self.algorithm_box.currentText()
        try:
            settings['hub'] = self.parent.parent.tree_widget.get_selected_hub()
        except Exception as e:
            if e == IndexError:
                log.warn('Select knobs before starting optimization!')
            elif e == KeyError:
                log.warn('Decentralized processes not yet supported.')
            return

        settings['algorithm_params'] = self.algorithm_table.get_params()
        settings['experiment_params'] = self.experiment_table.get_params()
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
