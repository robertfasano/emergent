#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import types
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
        QGroupBox, QHBoxLayout, QLabel, QLineEdit, QTreeView, QPushButton, QTableView,QVBoxLayout,
        QWidget, QMenu, QAction, QTreeWidget, QTreeWidgetItem)
from PyQt5.QtCore import *
import functools

class OptimizerWindow(QWidget):
    def __init__(self, control):
        QWidget.__init__(self)
        self.setWindowTitle('EMERGENT: Optimizer')
        with open('../../gui/stylesheet.txt',"r") as file:
            self.setStyleSheet(file.read())

        self.control = control

        self.label = QLabel('test')
        layout = QHBoxLayout(self)
        layout.addWidget(self.label)
