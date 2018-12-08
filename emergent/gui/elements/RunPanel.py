from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QTableWidget, QTableWidgetItem, QHBoxLayout, QCheckBox, QTabWidget, QLineEdit, QSlider)
from PyQt5.QtCore import *
from emergent.archetypes.optimizer import Optimizer
from emergent.archetypes.parallel import ProcessHandler
from emergent.archetypes.sampler import Sampler

from emergent.utility import list_algorithms, list_triggers
import inspect
import json
import logging as log
import time
from scipy.stats import linregress
import numpy as np
import datetime
import json

class RunLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent
        self.name = 'Run'
        self.cost_box = QComboBox()

        self.addWidget(self.cost_box)
        self.cost_box.currentTextChanged.connect(lambda: self.parent.update_experiment(self))

        ''' Experiment parameters '''
        self.epl = QTableWidget()
        self.addWidget(self.epl)
        self.epl.insertColumn(0)
        self.epl.insertColumn(1)
        self.epl.setHorizontalHeaderLabels(['Parameter', 'Value'])
        self.epl.horizontalHeader().setStretchLastSection(True)

        self.runIterationsLayout = QHBoxLayout()
        self.runIterationsLayout.addWidget(QLabel('Iterations'))
        self.runIterationsSlider = QSlider(Qt.Horizontal)
        self.runIterationsSlider.valueChanged.connect(self.updateIterations)
        self.runIterationsSlider.setRange(1,8)
        self.runIterationsSlider.setSingleStep(1)
        self.runIterationsLayout.addWidget(self.runIterationsSlider)
        self.runIterationsEdit = QLineEdit('')
        self.runIterationsLayout.addWidget(self.runIterationsEdit)
        self.runIterationsSlider.setValue(8)
        self.addLayout(self.runIterationsLayout)

        self.runButtonsLayout = QHBoxLayout()
        self.runExperimentButton = QPushButton('Run')
        self.runExperimentButton.clicked.connect(lambda: parent.start_process(process='run', panel = self, settings = {}))

        self.runButtonsLayout.addWidget(self.runExperimentButton)
        self.addLayout(self.runButtonsLayout)

    def get_settings_from_gui(self):
        settings = {}
        settings['cost_name'] = self.cost_box.currentText()
        try:
            settings['control'] = self.parent.parent.treeWidget.get_selected_control()
        except IndexError:
            log.warn('Select inputs before starting optimization!')
            return
        settings['state'] = settings['control'].state
        settings['cost_params'] = self.parent.get_cost_params(self)
        if 'cycles per sample' not in settings['cost_params']:
            settings['cost_params']['cycles per sample'] = 1#int(self.cycles_per_sample_edit.text())
        settings['iterations'] = self.runIterationsEdit.text()
        if settings['iterations'] != 'Continuous':
            settings['iterations'] = int(settings['iterations'])
        settings['callback'] = None
        settings['algo_params'] = {}

        return settings

    def run_process(self, sampler, settings, index, t, stopped = None):
        count = 0
        control = settings['control']
        cost_params = settings['cost_params']
        while sampler.active:
            state = control.state
            result = sampler._cost(state, norm=False)
            count += 1
            if type(settings['iterations']) is int:
                if count >= settings['iterations']:
                    break
        control.samplers[index]['status'] = 'Done'
        sampler.log(t.replace(':','') + ' - ' + sampler.cost.__name__)
        sampler.active = False

    def stop_experiment(self):
        self._quit_thread(self.run_experiment)

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
