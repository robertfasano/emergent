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
from emergent.remote.NetworkPanel import NodeTree
from emergent.archetypes.client import Client
import os
import psutil
import sys

class Viewer(QMainWindow):
    def __init__(self, app):
        QMainWindow.__init__(self)
        self.setWindowTitle('EMERGENT: Remote viewer')
        with open('../gui/stylesheet.txt',"r") as file:
            self.setStyleSheet(file.read())
        self.app = app
        self.widget = QWidget()
        self.setWindowIcon(QIcon('gui/media/icon.png'))
        self.setCentralWidget(self.widget)
        layout= QHBoxLayout(self.widget)

        self.client = Client()

        width_fraction = 0.72
        height_fraction = width_fraction/1.618
        width = self.app.desktop().screenGeometry().width()*width_fraction
        height = self.app.desktop().screenGeometry().height()*height_fraction
        self.resize(width, height)

        self.button = QPushButton('get_state')
        self.button.clicked.connect(self.client.get_state)
        layout.addWidget(self.button)

        ''' Create QTreeWidget '''
        self.treeLayout = QVBoxLayout()
        self.treeWidget = NodeTree(self)
        self.treeLayout.addWidget(self.treeWidget)
        layout.addLayout(self.treeLayout)
