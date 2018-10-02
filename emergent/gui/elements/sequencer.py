from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QHBoxLayout, QCheckBox, QTabWidget, QLineEdit)
from PyQt5.QtCore import *
from emergent.archetypes.optimizer import Optimizer
from emergent.archetypes.parallel import ProcessHandler
import inspect
import json
import logging as log
import time
from scipy.stats import linregress
import numpy as np

class SequenceBox(QComboBox):
    def __init__(self, name, parent, sequence_type):
        super().__init__()
        self.parent = parent
        self.name = name
        for item in ['constant', 'linear', 'pointwise']:
            self.addItem(item)
        index = self.findText(sequence_type)
        self.currentTextChanged.connect(self.change_sequence_type)
        self.setCurrentIndex(index)

    def change_sequence_type(self):
        new = self.currentText()
        self.parent.change_sequence_type(self.name, new)

class SequencerLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent

        self.addWidget(QLabel('Sequencing'))
        self.labels = {}
        self.inputLayouts = {}
        self.sequenceTypeBoxes = {}
        self.stepsEdit = {}
        self.parent.openSequencerSignal.connect(self.open)
        self.setVisible(False)


    def add_input(self, name):
        self.labels[name] = QLabel(name)
        self.addWidget(self.labels[name])
        box = SequenceBox(name, self, self.node.children[name].sequence_type)
        self.sequenceTypeBoxes[name] = box
        self.addWidget(box)
        self.inputLayouts[name] = QHBoxLayout()
        self.inputLayouts[name].addWidget(QLabel('Steps'))
        self.stepsEdit[name] = QLineEdit('2')
        self.inputLayouts[name].addWidget(self.stepsEdit[name])
        self.addLayout(self.inputLayouts[name])

    def delete_input(self, name):
        layout = self.inputLayouts[name]
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            widget.deleteLater()
            del widget

        self.labels[name].deleteLater()
        del self.labels[name]

        self.sequenceTypeBoxes[name].deleteLater()
        del self.sequenceTypeBoxes[name]

    def change_sequence_type(self, name, new_type):
        print('Changing %s to %s'%(name, new_type))
        input = self.node.children[name]
        input.sequence_type = new_type


        if new_type == 'constant':
            input.sequence = [(0,input.state)]
        if new_type == 'linear':
            input.sequence = [(0,input.state), (1,input.state)]
        elif new_type == 'pointwise':
            input.sequence = 0.5 * np.ones(int(self.stepsEdit[name].text()))
    def open(self, node):
        self.node = node['input']       #actually device node
        self.node.sequencer = self
        if not self.visible:
            for input in self.node.children:
                self.add_input(input)
        else:
            for input in self.node.children:
                self.delete_input(input)
        self.toggleVisibility()

    def toggleVisibility(self):
        self.setVisible(1-self.visible)

    def setVisible(self, tf):
        ''' bool tf '''
        self.visible = tf
        for i in range(self.count()):
            widget = self.itemAt(i).widget()
            if widget is not None:
                if tf:
                    widget.show()
                else:
                    widget.hide()
            else:
                for j in range(self.itemAt(i).count()):
                    widget = self.itemAt(i).itemAt(j).widget()
                    if tf:
                        widget.show()
                    else:
                        widget.hide()
