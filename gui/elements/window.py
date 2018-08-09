#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
import sys
import types
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont
from PyQt5.QtWidgets import (QApplication, QAbstractItemView,QCheckBox, QComboBox, QGridLayout,
        QGroupBox, QHBoxLayout, QLabel, QTextEdit, QTreeView, QPushButton, QTableView,QVBoxLayout,
        QWidget, QMenu, QAction, QTreeWidget, QTreeWidgetItem, QMainWindow, QStatusBar)
from PyQt5.QtCore import *
import json
from archetypes.optimizer import Optimizer
from gui.elements.optimizer import OptimizerLayout
from gui.elements.sequencer import SequencerLayout
from gui.elements.treeview import TreeLayout
import os
import psutil

class MainFrame(QMainWindow):
    def __init__(self, app, tree, controls):
        QMainWindow.__init__(self)
        self.setWindowTitle('EMERGENT')
        with open('gui/stylesheet.txt',"r") as file:
            self.setStyleSheet(file.read())
        self.controls = controls
        self.app = app
        self.widget = QWidget()
        self.setCentralWidget(self.widget)
        layout= QHBoxLayout(self.widget)

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
        self.treeLayout = TreeLayout(tree, controls, self)
        layout.addLayout(self.treeLayout)

        ''' Create optimizer layout '''
        self.optimizer = OptimizerLayout(self)
        layout.addLayout(self.optimizer)

        ''' Create sequencer layout '''
        self.sequencer = SequencerLayout(self)
        layout.addLayout(self.sequencer)

    def get_system_stats(self):
        mem = 'Memory usage: %.2f GB'%(psutil.Process(os.getpid()).memory_info()[0]/2.**30)
        cpu = 'CPU usage: %.2f%%'%psutil.cpu_percent()

        self.systemStats.setText(mem + '  |  ' + cpu)
