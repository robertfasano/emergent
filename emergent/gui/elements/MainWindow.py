#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
import sys
import types
from PyQt5.QtGui import QIcon, QStandardItem, QStandardItemModel, QFont
from PyQt5.QtWidgets import (QApplication, QAbstractItemView,QCheckBox, QComboBox, QGridLayout,
        QGroupBox, QHBoxLayout, QLabel, QTextEdit, QTreeView, QPushButton, QTableView,QVBoxLayout,
        QWidget, QMenu, QAction, QTreeWidget, QTreeWidgetItem, QMainWindow, QStatusBar)
from PyQt5.QtCore import *
import json
from emergent.archetypes.optimizer import Optimizer
from emergent.gui.elements.ExperimentPanel import OptimizerLayout
# from emergent.gui.elements.sequencer import SequencerLayout
from emergent.gui.elements.NetworkPanel import NodeTree
import os
import psutil
import sys

class MainFrame(QMainWindow):
    def __init__(self, app, tree, controls):
        QMainWindow.__init__(self)
        self.setWindowTitle('EMERGENT: %s'%sys.argv[1])
        with open('gui/stylesheet.txt',"r") as file:
            self.setStyleSheet(file.read())
        self.controls = controls
        self.app = app
        self.widget = QWidget()
        self.setWindowIcon(QIcon('gui/media/icon.png'))
        self.setCentralWidget(self.widget)
        layout= QHBoxLayout(self.widget)
        width = 1000
        self.resize(width, width/1.618)
        ''' Create status bar '''
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.systemStats = QLabel()
        self.statusBar.addWidget(self.systemStats)
        self.get_system_stats()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.get_system_stats)
        self.timer.start(5*1000)

        ''' Create QTreeWidget '''
        self.treeLayout = QVBoxLayout()
        self.treeWidget = NodeTree(tree, controls, self)
        self.treeLayout.addWidget(self.treeWidget)
        layout.addLayout(self.treeLayout)

        self.saveButton = QPushButton('Save')
        self.saveButton.clicked.connect(self.save)
        self.treeLayout.addWidget(self.saveButton)

        ''' Create optimizer layout '''
        self.optimizer = OptimizerLayout(self)
        layout.addLayout(self.optimizer)

        ''' Create sequencer layout '''
        # self.sequencer = SequencerLayout(self)
        # layout.addLayout(self.sequencer)

    def get_system_stats(self):
        mem = 'Memory usage: %.2f GB'%(psutil.Process(os.getpid()).memory_info()[0]/2.**30)
        cpu = 'CPU usage: %.2f%%'%psutil.cpu_percent()

        self.systemStats.setText(mem + '  |  ' + cpu)

    def save(self):
        for c in self.controls.values():
            c.save()
