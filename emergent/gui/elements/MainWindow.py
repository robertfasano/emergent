#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
import sys
import types
from PyQt5.QtGui import QIcon, QStandardItem, QStandardItemModel, QFont, QFontDatabase
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QTreeView, QPushButton, QVBoxLayout,
        QWidget, QMenu, QAction, QTreeWidget, QTreeWidgetItem, QMainWindow, QStatusBar, QMenuBar)
from PyQt5.QtCore import *
import json
from emergent.gui.elements import ExperimentLayout, HistoryPanel, ServoLayout, NodeTree
import os
import psutil
import sys

class MainFrame(QMainWindow):
    def __init__(self, app, network):
        QMainWindow.__init__(self)
        self.setWindowTitle('EMERGENT: %s'%sys.argv[1])
        QFontDatabase.addApplicationFont('gui/media/Exo2-Light.ttf')
        with open('gui/stylesheet.txt',"r") as file:
            self.setStyleSheet(file.read())
        self.network = network
        self.app = app
        self.widget = QWidget()
        self.setWindowIcon(QIcon('gui/media/icon.png'))
        self.setCentralWidget(self.widget)
        master_layout = QVBoxLayout(self.widget)
        layout= QHBoxLayout()
        master_layout.addLayout(layout)
        width_fraction = 0.72
        height_fraction = width_fraction/1.618
        width = self.app.desktop().screenGeometry().width()*width_fraction
        height = self.app.desktop().screenGeometry().height()*height_fraction
        width = 1080
        height = 720
        self.resize(width, height)

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
        self.treeWidget = NodeTree(self)
        self.treeLayout.addWidget(self.treeWidget)
        layout.addLayout(self.treeLayout)

        ''' Experiment interface '''
        self.experiment_layout = QVBoxLayout()
        layout.addLayout(self.experiment_layout)

        ''' Create optimizer layout '''
        self.experimentPanel = ExperimentLayout(self)
        self.experiment_layout.addLayout(self.experimentPanel)

        ''' Create history panel '''
        self.historyPanel = HistoryPanel(self)
        self.experiment_layout.addLayout(self.historyPanel)

        ''' Create menu bar '''
        self.menuBar = QMenuBar()
        self.setMenuBar(self.menuBar)
        self.network_menu = self.menuBar.addMenu('Network')
        self.algorithm_menu = self.menuBar.addMenu('Algorithm')
        self.experiment_menu = self.menuBar.addMenu('Experiment')
        self.task_menu = self.menuBar.addMenu('Tasks')

        self.create_menu_action(self.task_menu, 'Load task', self.historyPanel.load_task)
        self.create_menu_action(self.network_menu, 'Save state', self.network.save)
        self.create_menu_action(self.algorithm_menu, 'Save parameters', lambda: self.experimentPanel.save_params(self.experimentPanel.panel, 'algorithm'))
        self.create_menu_action(self.algorithm_menu, 'Reset parameters', lambda: self.experimentPanel.update_algorithm_and_experiment(self.experimentPanel.panel, default=True, update_experiment=False))
        self.create_menu_action(self.experiment_menu, 'Save parameters', lambda: self.experimentPanel.save_params(self.experimentPanel.panel, 'experiment'))
        self.create_menu_action(self.experiment_menu, 'Reset parameters', lambda: self.experimentPanel.update_algorithm_and_experiment(self.experimentPanel.panel, default=True, update_algorithm=False))

    def create_menu_action(self, menu, name, function):
        action = menu.addAction(name)
        action.triggered.connect(function)

    def get_system_stats(self):
        mem = 'Memory usage: %.2f GB'%(psutil.Process(os.getpid()).memory_info()[0]/2.**30)
        cpu = 'CPU usage: %.2f%%'%psutil.cpu_percent()

        self.systemStats.setText(mem + '  |  ' + cpu)

    def servo(self):
        if self.show_servo.isChecked():
            self.setLayoutVisible(self.servoPanel, True)
        else:
            self.setLayoutVisible(self.servoPanel, False)

    def tasks(self):
        if self.show_tasks.isChecked():
            self.setLayoutVisible(self.historyPanel, True)
        else:
            self.setLayoutVisible(self.historyPanel, False)

    def setLayoutVisible(self, layout, visible):
        for i in range(layout.count()):
            w = layout.itemAt(i).widget()
            if w is not None:
                w.setVisible(visible)
            else:
                try:
                    self.setLayoutVisible(layout.itemAt(i), visible)
                except Exception as e:
                    print(e)
