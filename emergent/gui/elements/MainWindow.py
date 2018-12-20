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
from emergent.gui.elements import ExperimentLayout, TaskPanel, ServoLayout, NodeTree, MonitorPanel
import os
import psutil
import sys

class MainFrame(QMainWindow):
    def __init__(self, app, network):
        QMainWindow.__init__(self)
        self.network = network
        self.app = app

        ''' Set window style '''
        self.setWindowTitle('EMERGENT: %s @ %s:%i'%(network.name, network.addr, network.port))
        QFontDatabase.addApplicationFont('gui/media/Exo2-Light.ttf')
        with open('gui/stylesheet.txt',"r") as file:
            self.setStyleSheet(file.read())
        self.central_widget = QWidget()
        self.setWindowIcon(QIcon('gui/media/icon.png'))
        self.setCentralWidget(self.central_widget)
        layout= QHBoxLayout(self.central_widget)
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
        self.treeWidget = NodeTree(self.network, self)
        self.treeLayout.addWidget(self.treeWidget)
        layout.addLayout(self.treeLayout)

        ''' Experiment interface '''
        self.experiment_layout = QVBoxLayout()
        layout.addLayout(self.experiment_layout)
        self.experimentPanel = ExperimentLayout(self)
        self.experiment_layout.addLayout(self.experimentPanel)

        ''' Create task panel '''
        self.taskPanel = TaskPanel(self)
        self.experiment_layout.addLayout(self.taskPanel)

        ''' Create monitor panel '''
        self.monitorPanel = MonitorPanel(self)
        layout.addLayout(self.monitorPanel)


        ''' Create menu bar '''
        self.menuBar = QMenuBar()
        self.setMenuBar(self.menuBar)
        self.network_menu = self.menuBar.addMenu('Network')
        self.algorithm_menu = self.menuBar.addMenu('Algorithm')
        self.experiment_menu = self.menuBar.addMenu('Experiment')
        self.task_menu = self.menuBar.addMenu('Tasks')

        self.create_menu_action(self.task_menu, 'Load task', self.taskPanel.load_task)
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
