''' The MeasureLayout allows users to run experiments with parameters defined in the GUI.
    Experiments can be run for a defined number of iterations or continuously. '''

from PyQt5.QtWidgets import (QComboBox, QLabel, QLineEdit, QPushButton, QVBoxLayout,
        QTableWidget, QTableWidgetItem, QHBoxLayout, QSlider, QMenu)
from PyQt5.QtCore import *
import logging as log
import datetime
from emergent.dashboard.structures.parameter_table import ParameterTable
from emergent.dashboard.structures.icon_button import IconButton

class MeasureLayout(QVBoxLayout):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        self.parent = parent
        self.name = 'Measure'
        self.trigger = None
        box_layout = QHBoxLayout()
        self.addLayout(box_layout)
        self.experiment_box = QComboBox()

        box_layout.addWidget(self.experiment_box)
        self.experiment_box.currentTextChanged.connect(self.update_params)
        box_layout.addWidget(IconButton('dashboard/gui/media/Material/content-save-outline.svg', self.save_params))
        box_layout.addWidget(IconButton('dashboard/gui/media/Material/content-undo.svg', self.reset_params))
        # box_layout.addWidget(IconButton('dashboard/gui/media/Material/outline-repeat_one.svg', self.update_params))
        trigger_button = IconButton('dashboard/gui/media/Material/outline-hourglass-empty.svg', self.update_params)
        box_layout.addWidget(trigger_button)    # placeholder
        box_layout.addWidget(IconButton('dashboard/gui/media/Material/outline-play-arrow.svg', lambda: parent.start_process(process='measure')))

        self.trigger_menu = QMenu()
        self.trigger_menu.addAction('No triggers defined')

        trigger_button.setMenu(self.trigger_menu)

        ''' Experiment parameters '''
        self.experiment_table = ParameterTable()
        self.addWidget(self.experiment_table)

        # self.runIterationsLayout = QHBoxLayout()
        # label = QLabel('Iterations')
        # self.runIterationsLayout.addWidget(label)
        # label.setStyleSheet('color:"#000000"; font-weight: light; font-family: "Exo 2"; font-size: 14px; background-color: transparent')
        # self.runIterationsSlider = QSlider(Qt.Horizontal)
        # self.runIterationsSlider.setStyleSheet('background-color: transparent')
        # self.runIterationsSlider.valueChanged.connect(self.updateIterations)
        # self.runIterationsSlider.setRange(1,8)
        # self.runIterationsSlider.setSingleStep(1)
        # self.runIterationsLayout.addWidget(self.runIterationsSlider)
        # self.runIterationsEdit = QLineEdit('')
        # self.runIterationsEdit.setStyleSheet('color:"#000000"; font-weight: light; font-family: "Exo 2"; font-size: 14px; background-color: rgba(255, 255, 255, 80%)')
        # self.runIterationsLayout.addWidget(self.runIterationsEdit)
        # self.runIterationsSlider.setValue(8)
        # self.addLayout(self.runIterationsLayout)

    def set_trigger(self, trigger):
        self.trigger = trigger

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
        settings['experiment']['params']['iterations'] = 'Continuous'

        # settings['experiment']['params']['iterations'] = self.runIterationsEdit.text()
        # if settings['experiment']['params']['iterations'] != 'Continuous':
        #     settings['experiment']['params']['iterations'] = int(settings['experiment']['params']['iterations'])
        settings['process']['callback'] = None

        if self.trigger is not None:
            settings['process']['trigger'] = self.trigger
        settings['process']['type'] = 'measure'

        return settings

    # def updateIterations(self):
    #     try:
    #         val = self.runIterationsSlider.value()
    #         text = {}
    #         for i in range(1,8):
    #             text[i] = str(2**i)
    #         text[8] = 'Continuous'
    #         self.runIterationsEdit.setText(text[val])
    #     except AttributeError:
    #         return

    def update_params(self):
        experiment = self.experiment_box.currentText()
        if experiment == '':
            return
        hub = self.parent.dashboard.tree_widget.get_selected_hub()
        d = self.parent.dashboard.get('hubs/%s/experiments/%s'%(hub, experiment))
        self.experiment_table.set_parameters(d['experiment'])

    def reset_params(self):
        experiment = self.experiment_box.currentText()
        if experiment == '':
            return
        hub = self.parent.dashboard.tree_widget.get_selected_hub()
        d = self.parent.dashboard.get('hubs/%s/experiments/%s/default'%(hub, experiment))
        self.experiment_table.set_parameters(d['experiment'])

    def save_params(self):
        experiment = self.experiment_box.currentText()
        if experiment == '':
            return
        hub = self.parent.dashboard.tree_widget.get_selected_hub()
        params = self.experiment_table.get_params()
        self.parent.dashboard.post('hubs/%s/experiments/%s'%(hub, experiment), {'params': params})
