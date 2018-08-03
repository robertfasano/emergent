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
from archetypes.Optimizer import Optimizer
from gui.elements.optimizer import OptimizerLayout
from gui.elements.treeview import TreeLayout

class MainFrame(QWidget):
    def __init__(self, tree, control):
        QWidget.__init__(self)
        self.setWindowTitle('EMERGENT')
        with open('gui/stylesheet.txt',"r") as file:
            self.setStyleSheet(file.read())
        self.control = control 

        layout= QHBoxLayout(self)

        ''' Create QTreeWidget '''
        self.treeLayout = TreeLayout(tree, control)
        layout.addLayout(self.treeLayout)

        ''' Create optimizer layout '''
        self.optimizer = OptimizerLayout(self)
        layout.addLayout(self.optimizer)