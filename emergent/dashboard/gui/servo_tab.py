''' The ServoLayout allows the user to start servo processes, such as digital PID
    loops, targeting an @error method with specified parameters. '''

from PyQt5.QtWidgets import (QComboBox, QLabel, QPushButton, QVBoxLayout,
        QTableWidget, QGridLayout, QTableWidgetItem, QHBoxLayout)
from PyQt5.QtCore import *
import logging as log
import datetime
from emergent.gui.elements.ParameterTable import ParameterTable
from emergent.modules.parallel import ProcessHandler
from emergent.utilities import recommender

class ServoLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent
        self.name = 'Servo'
        layout = QGridLayout()
        self.addLayout(layout)

        ''' Algorithm/experiment select layout '''
        self.error_box = QComboBox()
        self.servo_box = QComboBox()
        layout.addWidget(self.servo_box, 0, 0)
        layout.addWidget(self.error_box, 0, 1)

        ''' Algorithm parameters '''
        self.servo_table = ParameterTable()
        layout.addWidget(self.servo_table, 1, 0)

        ''' Experiment parameters '''
        self.error_table = ParameterTable()
        layout.addWidget(self.error_table, 1, 1)

        self.servo_box.currentTextChanged.connect(lambda: self.parent.update_servo(self))
        self.error_box.currentTextChanged.connect(lambda: self.parent.update_error(self))

        optimizeButtonsLayout = QHBoxLayout()
        self.optimizer_button = QPushButton('Go!')
        self.optimizer_button.clicked.connect(lambda: parent.start_process(process='servo'))

        optimizeButtonsLayout.addWidget(self.optimizer_button)
        self.addLayout(optimizeButtonsLayout)

    def get_settings_from_gui(self):
        settings = {'experiment': {}, 'servo': {}, 'process': {}}
        settings['state'] = self.parent.dashboard.tree_widget.get_selected_state()
        settings['experiment']['name'] = self.error_box.currentText()
        settings['servo']['name'] = self.servo_box.currentText()

        try:
            settings['hub'] = self.parent.dashboard.tree_widget.get_selected_hub()
        except Exception as e:
            if e == IndexError:
                log.warn('Select inputs before starting optimization!')
            elif e == KeyError:
                log.warn('Decentralized processes not yet supported.')
            return

        settings['servo']['params'] = self.servo_table.get_params()
        settings['experiment']['params'] = self.error_table.get_params()

        settings['process']['callback'] = None
        settings['process']['type'] = 'servo'

        return settings
