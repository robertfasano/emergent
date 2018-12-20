from PyQt5.QtWidgets import (QComboBox, QLabel, QLineEdit, QPushButton, QVBoxLayout,
        QTableWidget, QTableWidgetItem, QHBoxLayout, QSlider)
from PyQt5.QtCore import *
from emergent.modules import ProcessHandler, Sampler
import inspect
import json
import logging as log
import time
from scipy.stats import linregress
import numpy as np
import datetime
import json
from emergent.gui.elements.ParameterTable import ParameterTable

class RunLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent
        self.name = 'Run'
        self.experiment_box = QComboBox()

        self.addWidget(self.experiment_box)
        self.experiment_box.currentTextChanged.connect(lambda: self.parent.update_experiment(self))

        ''' Experiment parameters '''
        self.experiment_table = ParameterTable()
        self.addWidget(self.experiment_table)

        self.runIterationsLayout = QHBoxLayout()
        label = QLabel('Iterations')
        self.runIterationsLayout.addWidget(label)
        label.setStyleSheet('color:"#000000"; font-weight: light; font-family: "Exo 2"; font-size: 14px; background-color: transparent')

        self.runIterationsSlider = QSlider(Qt.Horizontal)
        self.runIterationsSlider.setStyleSheet('background-color: transparent')

        self.runIterationsSlider.valueChanged.connect(self.updateIterations)
        self.runIterationsSlider.setRange(1,8)
        self.runIterationsSlider.setSingleStep(1)
        self.runIterationsLayout.addWidget(self.runIterationsSlider)
        self.runIterationsEdit = QLineEdit('')
        self.runIterationsEdit.setStyleSheet('color:"#000000"; font-weight: light; font-family: "Exo 2"; font-size: 14px; background-color: rgba(255, 255, 255, 80%)')

        self.runIterationsLayout.addWidget(self.runIterationsEdit)
        self.runIterationsSlider.setValue(8)
        self.addLayout(self.runIterationsLayout)

        self.runButtonsLayout = QHBoxLayout()
        self.runExperimentButton = QPushButton('Go!')
        self.runExperimentButton.clicked.connect(lambda: parent.start_process(process='run', settings = {}))

        self.runButtonsLayout.addWidget(self.runExperimentButton)
        self.addLayout(self.runButtonsLayout)

    def get_settings_from_gui(self):
        settings = {}
        settings['experiment_name'] = self.experiment_box.currentText()
        try:
            settings['hub'] = self.parent.parent.treeWidget.get_selected_hub()
        except Exception as e:
            if e == IndexError:
                log.warn('Select inputs before starting optimization!')
            elif e == KeyError:
                log.warn('Decentralized processes not yet supported.')
            return
        settings['state'] = settings['hub'].state
        settings['experiment_params'] = self.experiment_table.get_params()
        if 'cycles per sample' not in settings['experiment_params']:
            settings['experiment_params']['cycles per sample'] = 1#int(self.cycles_per_sample_edit.text())
        settings['experiment_params']['iterations'] = self.runIterationsEdit.text()
        if settings['experiment_params']['iterations'] != 'Continuous':
            settings['experiment_params']['iterations'] = int(settings['experiment_params']['iterations'])
        settings['callback'] = None
        settings['algorithm_params'] = {}

        return settings

    def run_process(self, sampler, stopped = None):
        count = 0
        while sampler.active:
            result = sampler._cost(sampler.hub.state, norm=False)
            count += 1
            if type(sampler.experiment_params['iterations']) is int:
                if count >= sampler.experiment_params['iterations']:
                    break
        sampler.log(sampler.start_time.replace(':','') + ' - ' + sampler.experiment.__name__)
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
