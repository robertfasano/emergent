#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
import sys
import types
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont
from PyQt5.QtWidgets import (QApplication, QAbstractItemView,QCheckBox, QComboBox, QGridLayout,
        QGroupBox, QHBoxLayout, QLabel, QTextEdit, QTreeView, QPushButton, QTableView,QVBoxLayout,
        QWidget, QMenu, QAction, QTreeWidget, QTreeWidgetItem)
from PyQt5.QtCore import *
import json
from archetypes.optimizer import Optimizer
from gui.elements.optimizer import OptimizerLayout
from gui.elements.sequencer import SequencerLayout
from gui.elements.treeview import TreeLayout

class MainFrame(QWidget):
    def __init__(self, app, tree, controls):
        QWidget.__init__(self)
        self.setWindowTitle('EMERGENT')
        with open('gui/stylesheet.txt',"r") as file:
            self.setStyleSheet(file.read())
        self.controls = controls
        self.app = app
        layout= QHBoxLayout(self)

        ''' Create QTreeWidget '''
        self.treeLayout = TreeLayout(tree, controls, self)
        layout.addLayout(self.treeLayout)

        ''' Create optimizer layout '''
        self.optimizer = OptimizerLayout(self)
        layout.addLayout(self.optimizer)

        ''' Create sequencer layout '''
        self.sequencer = SequencerLayout(self)
        layout.addLayout(self.sequencer)
