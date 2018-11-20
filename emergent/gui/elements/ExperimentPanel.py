from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QHBoxLayout, QCheckBox, QTabWidget, QLineEdit, QSlider)
from PyQt5.QtCore import *
from emergent.archetypes.optimizer import Optimizer
from emergent.gui.elements.OptimizeTab import OptimizeLayout
from emergent.archetypes.parallel import ProcessHandler
from emergent.gui.elements.ServoPanel import ServoLayout
from emergent.gui.elements.RunPanel import RunLayout

from emergent.utility import list_algorithms, list_triggers
import inspect
import json
import logging as log
import time
from scipy.stats import linregress
import numpy as np
import datetime

class ExperimentLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent
        self.cost_box = QComboBox()
        self.tabWidget = QTabWidget()
        self.addWidget(self.tabWidget)

        ''' Create Optimizer tab '''
        optimizeTab = QWidget()
        self.optimizePanel = OptimizeLayout(self)
        optimizeTab.setLayout(self.optimizePanel)
        self.tabWidget.addTab(optimizeTab, 'Optimize')

        ''' Create Servo tab '''
        servoTab = QWidget()
        self.servoPanel = ServoLayout(self)
        servoTab.setLayout(self.servoPanel)
        self.tabWidget.addTab(servoTab, 'Servo')

        ''' Create Run tab '''
        runTab = QWidget()
        self.runPanel = RunLayout(self)
        runTab.setLayout(self.runPanel)
        self.tabWidget.addTab(runTab, 'Run')

    def docstring_to_edit(self, f, edit):
        ''' Reads the signature of the method f, then prepares a human-readable format for
            the QLineEdit edit. '''
        args = inspect.signature(f).parameters
        args = list(args.items())
        arguments = []
        for a in args:
            name = a[0]
            if name == 'params':
                default = str(a[1])
                default = default.split('=')[1]
                default = default.replace('{', '')
                default = default.replace(',', '\n')
                default = default.replace('}', '')
                if edit is not None:
                    edit.setText(default)
