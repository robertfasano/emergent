''' The OptimizeTab allows the user to choose algorithms and their parameters and
    launch optimizations. '''
from PyQt5.QtWidgets import (QComboBox, QPushButton, QTabWidget, QVBoxLayout, QWidget,
        QTableWidgetItem, QTableWidget, QHBoxLayout, QGridLayout, QLabel, QMenu, QAction,
        QTreeWidget, QTreeWidgetItem, QAbstractItemView)
from PyQt5.QtCore import *
from PyQt5.QtGui import QCursor
from emergent.modules.parallel import ProcessHandler
import logging as log
import numpy as np
from emergent.dashboard.gui.parameter_table import ParameterTable
from emergent.utilities import recommender
import importlib, inspect

class CustomTree(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.itemDoubleClicked.connect(self.open_editor)

    def keyPressEvent(self, event):
        if event.key() == 16777220:
            self.update_editor()

    def update_editor(self):
        ''' Send actuate command and disable editing after the user presses return or clicks another node. '''
        col = self.currentIndex().column()
        self.last_item = self.current_item
        self.current_item = self.currentItem()
        self.closePersistentEditor(self.last_item, col)
        self.editorOpen = 0

    def open_editor(self):
        ''' Allow the currently-selected node to be edited. '''
        self.current_item = self.currentItem()
        self.currentValue = self.current_item.text(1)
        col = self.currentIndex().column()
        if col == 0:
            return
        if col in [1,2,3]:
            self.openPersistentEditor(self.current_item, col)
            self.editorOpen = 1

class PipelineLayout(QVBoxLayout):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)


        self.tree = CustomTree()
        self.tree.setColumnCount(2)
        header_item = QTreeWidgetItem(['Block', 'Parameter'])
        self.tree.setHeaderItem(header_item)
        self.tree.setDragEnabled(True)
        self.tree.viewport().setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QAbstractItemView.InternalMove)

        self.addWidget(self.tree)

    def add_block(self, d):
        name = d['name']
        root = QTreeWidgetItem([name])
        root.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled)
        root.setFlags(root.flags() & ~Qt.ItemIsSelectable)

        self.tree.insertTopLevelItems(self.tree.topLevelItemCount(), [root])

        params = self.get_params(name)
        for p in params:
            item = QTreeWidgetItem([p])
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled)
            item.setText(1, str(params[p]))

            root.addChild(item)

    def list_optimizers(self):
        module = importlib.import_module('emergent.pipeline.optimizers')
        names = []
        for a in dir(module):
            if '__' not in a:
                inst = getattr(module, a)
                if inspect.isclass(inst):
                    names.append(inst.__name__)
        return names

    def list_models(self):
        module = importlib.import_module('emergent.pipeline.models')
        names = []
        for a in dir(module):
            if '__' not in a:
                inst = getattr(module, a)
                if inspect.isclass(inst):
                    names.append(inst.__name__)
        return names

    def list_blocks(self):
        module = importlib.import_module('emergent.pipeline.blocks')
        names = []
        for a in dir(module):
            if '__' not in a:
                inst = getattr(module, a)
                if inspect.isclass(inst):
                    names.append(inst.__name__)
        return names

    def get_params(self, name):
        module = getattr(importlib.import_module('emergent.pipeline'), name)
        params = module().params

        params_dict = {}
        for p in params:
            params_dict[p] = params[p].value

        return params_dict

    def get_pipeline(self):
        pipeline = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            block = {'block': item.text(0), 'params': {}}
            for j in range(item.childCount()):
                block['params'][item.child(j).text(0)] = float(item.child(j).text(1))
            pipeline.append(block)

        return pipeline
