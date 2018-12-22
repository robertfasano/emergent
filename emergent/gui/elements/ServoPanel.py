''' The ServoLayout allows the user to start servo processes, such as digital PID
    loops, targeting an @error method with specified parameters. '''
    
from PyQt5.QtWidgets import (QComboBox, QLabel, QPushButton, QVBoxLayout,
        QTableWidget, QGridLayout, QTableWidgetItem, QHBoxLayout)
from PyQt5.QtCore import *
import logging as log
import datetime
from emergent.gui.elements.ParameterTable import ParameterTable

class ServoLayout(QVBoxLayout):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        self.parent = parent
        self.name = 'Servo'
        layout = QGridLayout()
        self.addLayout(layout)

        ''' Algorithm/experiment select layout '''
        self.experiment_box = QComboBox()
        self.algorithm_box = QComboBox()
        layout.addWidget(self.algorithm_box, 0, 0)
        layout.addWidget(self.experiment_box, 0, 1)

        ''' Algorithm parameters '''
        self.algorithm_table = ParameterTable()
        layout.addWidget(self.algorithm_table, 1, 0)

        ''' Experiment parameters '''
        self.experiment_table = ParameterTable()
        layout.addWidget(self.experiment_table, 1, 1)

        self.experiment_box.currentTextChanged.connect(lambda: self.parent.update_algorithm_and_experiment(self))

        optimizeButtonsLayout = QHBoxLayout()
        self.optimizer_button = QPushButton('Go!')
        self.optimizer_button.clicked.connect(lambda: parent.start_process(process='servo', settings = {}, load_from_gui=True))

        optimizeButtonsLayout.addWidget(self.optimizer_button)
        self.addLayout(optimizeButtonsLayout)

    def get_settings_from_gui(self):
        settings = {}
        settings['state'] = self.parent.parent.treeWidget.get_selected_state()
        settings['experiment_name'] = self.experiment_box.currentText()
        try:
            settings['hub'] = self.parent.parent.treeWidget.get_selected_hub()
        except Exception as e:
            if e == IndexError:
                log.warn('Select inputs before starting optimization!')
            elif e == KeyError:
                log.warn('Decentralized processes not yet supported.')
            return

        settings['algorithm_params'] = self.algorithm_table.get_params()
        settings['experiment_params'] = self.experiment_table.get_params()

        settings['callback'] = None
        return settings

    def run_process(self, sampler):
        sampler.algorithm.run(sampler.state)
        log.info('Optimization complete!')
        sampler.log(sampler.start_time.replace(':','') + ' - ' + sampler.experiment.__name__ + ' - ' + sampler.algorithm.name)
        sampler.active = False
