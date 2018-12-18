#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
import sys
import types
from PyQt5.QtGui import QIcon, QStandardItem, QStandardItemModel, QFont
from PyQt5.QtWidgets import (QApplication, QAbstractItemView,QCheckBox, QComboBox, QGridLayout,
        QGroupBox, QHBoxLayout, QLabel, QTextEdit, QTreeView, QPushButton, QTableView,QVBoxLayout,
        QWidget, QMenu, QAction, QTreeWidget, QTreeWidgetItem, QMainWindow, QStatusBar)
from PyQt5.QtCore import QTimer
import json
from emergent.gui.elements import NodeTree
from emergent.modules.client import Client
import os
import psutil
import sys
import logging as log

class RemoteViewer(QMainWindow):
    def __init__(self, app):
        QMainWindow.__init__(self)
        self.setWindowTitle('EMERGENT: Remote viewer')
        with open('gui/stylesheet.txt',"r") as file:
            self.setStyleSheet(file.read())
        self.app = app
        self.widget = QWidget()
        self.setWindowIcon(QIcon('gui/media/icon.png'))
        self.setCentralWidget(self.widget)
        layout= QHBoxLayout(self.widget)

        self.client = Client()

        self.resize(540, 720)

        self.network = self.client.get_network()


        ''' Create QTreeWidget '''
        self.treeLayout = QVBoxLayout()
        self.treeWidget = NodeTree(self.network)
        self.treeLayout.addWidget(self.treeWidget)

        layout.addLayout(self.treeLayout)

        ''' Setup auto-update '''
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(self.client.params['tick'])

    def update(self):
        if not self.isVisible():
            self.update_timer.stop()
            return
        try:
            self.network = self.client.get_network()
        except ConnectionRefusedError:
            log.warn('Server closed connection.')
            self.update_timer.stop()
        for hub in self.network.hubs.values():
            self.treeWidget.actuate(hub.name, hub.state)
