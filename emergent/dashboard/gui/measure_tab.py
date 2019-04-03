''' The MeasureLayout allows users to run experiments with parameters defined in the GUI.
    Experiments can be run for a defined number of iterations or continuously. '''

from PyQt5.QtWidgets import (QComboBox, QLabel, QLineEdit, QPushButton, QVBoxLayout,
        QTableWidget, QTableWidgetItem, QHBoxLayout, QSlider)
from PyQt5.QtCore import *
import logging as log
import datetime
from emergent.dashboard.structures.parameter_table import ParameterTable
from emergent.modules.parallel import ProcessHandler

class MeasureLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent
        self.name = 'Measure'
        self.experiment_box = QComboBox()

        self.addWidget(self.experiment_box)
        self.experiment_box.currentTextChanged.connect(self.update_params)

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

        self.runTriggerLayout = QHBoxLayout()
        label = QLabel('Trigger')
        self.runTriggerLayout.addWidget(label)
        label.setStyleSheet('color:"#000000"; font-weight: light; font-family: "Exo 2"; font-size: 14px; background-color: transparent')
        self.trigger_box = QComboBox()
        self.runTriggerLayout.addWidget(self.trigger_box)
        self.addLayout(self.runTriggerLayout)

        self.runButtonsLayout = QHBoxLayout()
        self.runExperimentButton = QPushButton('Go!')
        self.runExperimentButton.clicked.connect(lambda: parent.start_process(process='measure'))

        self.runButtonsLayout.addWidget(self.runExperimentButton)
        self.addLayout(self.runButtonsLayout)

    def get_settings_from_gui(self):
        settings = {'experiment': {}, 'process': {}}
        settings['experiment']['name'] = self.experiment_box.currentText()
        settings['state'] = self.parent.dashboard.tree_widget.get_selected_state()
        try:
            settings['hub'] = self.parent.dashboard.tree_widget.currentItem().parent().parent().text(0)
        except Exception as e:
            if e == IndexError:
                log.warn('Select knobs before starting optimization!')
            elif e == KeyError:
                log.warn('Decentralized processes not yet supported.')
            return settings

        settings['experiment']['params'] = self.experiment_table.get_params()
        settings['experiment']['params']['iterations'] = self.runIterationsEdit.text()
        if settings['experiment']['params']['iterations'] != 'Continuous':
            settings['experiment']['params']['iterations'] = int(settings['experiment']['params']['iterations'])
        settings['process']['callback'] = None

        if self.trigger_box.currentText() != '':
            settings['process']['trigger'] = self.trigger_box.currentText()
        settings['process']['type'] = 'measure'

        return settings

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

    def update_params(self):
        experiment = self.experiment_box.currentText()
        if experiment == '':
            return
        hub = self.parent.dashboard.tree_widget.get_selected_hub()
        d = self.parent.dashboard.get('hubs/%s/experiments/%s'%(hub, experiment))
        self.experiment_table.set_parameters(d['experiment'])
