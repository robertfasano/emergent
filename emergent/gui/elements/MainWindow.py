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
    def __init__(self, app, tree, controls):
        QMainWindow.__init__(self)
        self.setWindowTitle('EMERGENT: %s'%sys.argv[1])
        QFontDatabase.addApplicationFont('gui/media/Exo2-Thin.ttf')
        with open('gui/stylesheet.txt',"r") as file:
            self.setStyleSheet(file.read())
        self.controls = controls
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
        width = 1440
        height = 720
        self.resize(width, height)


        # self.viewMenu = self.menuBar.addMenu('View')
        # # optimizer = self.viewMenu.addAction("Optimizer")
        # self.show_servo = self.viewMenu.addAction("Servo")
        # self.show_servo.setCheckable(True)
        # self.show_servo.triggered.connect(self.servo)
        # self.show_servo.setChecked(True)
        #
        # self.show_tasks = self.viewMenu.addAction("Tasks")
        # self.show_tasks.setCheckable(True)
        # self.show_tasks.triggered.connect(self.tasks)
        # self.show_tasks.setChecked(True)


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

        # self.saveButton = QPushButton('Save')
        # self.saveButton.clicked.connect(self.save)
        # self.treeLayout.addWidget(self.saveButton)

        ''' Create optimizer layout '''
        self.optimizer = ExperimentLayout(self)
        layout.addLayout(self.optimizer)

        ''' Create sequencer layout '''
        # self.sequencer = SequencerLayout(self)
        # layout.addLayout(self.sequencer)

        ''' Create history panel '''
        self.historyPanel = HistoryPanel(self)
        layout.addLayout(self.historyPanel)

        ''' Create menu bar '''
        self.menuBar = QMenuBar()
        self.setMenuBar(self.menuBar)
        self.network_menu = self.menuBar.addMenu('Network')
        self.algorithm_menu = self.menuBar.addMenu('Algorithm')
        self.experiment_menu = self.menuBar.addMenu('Experiment')

        self.task_menu = self.menuBar.addMenu('Tasks')

        self.save_action = self.network_menu.addAction('Save state')
        self.save_action.triggered.connect(self.save)

        self.save_algorithm_action = self.algorithm_menu.addAction('Save parameters')

        self.reset_algorithm_action = self.algorithm_menu.addAction('Reset parameters')


        self.save_experiment_action = self.experiment_menu.addAction('Save parameters')
        self.reset_experiment_action = self.experiment_menu.addAction('Reset parameters')

        self.save_experiment_action.triggered.connect(lambda: self.optimizer.save_params(self.optimizer.panel, 'experiment'))
        self.save_algorithm_action.triggered.connect(lambda: self.optimizer.save_params(self.optimizer.panel, 'algorithm'))

        self.reset_experiment_action.triggered.connect(lambda: self.optimizer.update_algorithm_and_experiment(self.optimizer.panel, default=True, update_algorithm=False))
        self.reset_algorithm_action.triggered.connect(lambda: self.optimizer.update_algorithm_and_experiment(self.optimizer.panel, default=True, update_experiment=False))

    def get_system_stats(self):
        mem = 'Memory usage: %.2f GB'%(psutil.Process(os.getpid()).memory_info()[0]/2.**30)
        cpu = 'CPU usage: %.2f%%'%psutil.cpu_percent()

        self.systemStats.setText(mem + '  |  ' + cpu)

    def save(self):
        for c in self.controls.values():
            c.save()

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
