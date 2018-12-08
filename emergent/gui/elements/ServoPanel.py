from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QTableWidget, QGridLayout, QTableWidgetItem, QHBoxLayout, QCheckBox, QTabWidget, QLineEdit, QSlider)
from PyQt5.QtCore import *
from emergent.archetypes.sampler import Sampler
from emergent.archetypes.parallel import ProcessHandler
import inspect
import json
import logging as log
import time
from scipy.stats import linregress
import numpy as np
import datetime
import json

class ServoLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent
        self.name = 'Servo'
        layout = QGridLayout()
        self.addLayout(layout)

        ''' Algorithm/experiment select layout '''
        self.cost_box = QComboBox()
        self.algorithm_box = QComboBox()
        layout.addWidget(self.algorithm_box, 0, 0)
        layout.addWidget(self.cost_box, 0, 1)

        ''' Algorithm parameters '''
        self.apl = QTableWidget()
        layout.addWidget(self.apl, 1, 0)
        self.apl.insertColumn(0)
        self.apl.insertColumn(1)
        self.apl.setHorizontalHeaderLabels(['Parameter', 'Value'])
        self.apl.horizontalHeader().setStretchLastSection(True)

        ''' Experiment parameters '''
        self.epl = QTableWidget()
        layout.addWidget(self.epl, 1, 1)
        self.epl.insertColumn(0)
        self.epl.insertColumn(1)
        self.epl.setHorizontalHeaderLabels(['Parameter', 'Value'])
        self.epl.horizontalHeader().setStretchLastSection(True)

        self.cost_box.currentTextChanged.connect(lambda: self.parent.update_algorithm_and_experiment(self))

        optimizeButtonsLayout = QHBoxLayout()
        self.optimizer_button = QPushButton('Go!')
        self.optimizer_button.clicked.connect(lambda: parent.start_process(process='servo', panel = self, settings = {}))

        optimizeButtonsLayout.addWidget(self.optimizer_button)
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

        settings['algo_params'] = self.parent.get_params(self)
        settings['cost_params'] = self.parent.get_cost_params(self)

        settings['callback'] = None
        return settings

    def run_process(self, sampler, settings, index, t):
        settings['algorithm'](settings['state'], settings['cost'], settings['algo_params'], settings['cost_params'], callback = settings['callback'])
        log.info('Optimization complete!')
        settings['control'].samplers[index]['status'] = 'Done'
        sampler.log(t.replace(':','') + ' - ' + settings['cost_name'] + ' - ' + settings['algorithm'].__name__)
        sampler.active = False
