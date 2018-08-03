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
from emergent.archetypes.Optimizer import Optimizer

class MainFrame(QWidget):
    def __init__(self, tree, control):
        QWidget.__init__(self)
        self.setWindowTitle('EMERGENT')
        with open('../../gui/stylesheet.txt',"r") as file:
            self.setStyleSheet(file.read())

        self.control = control
        self.control.window = self
        self.tree = tree

        self.currentItem = None
        self.lastItem = None
        layout= QHBoxLayout(self)

        ''' Create QTreeWidget '''
        self.treeWidget = QTreeWidget()
        self.treeWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.treeWidget.setColumnCount(2)
        self.treeWidget.setHeaderLabels(["Node", "Value"])
        self.treeWidget.header().resizeSection(1,60)
        self.treeWidget.itemDoubleClicked.connect(self.open_editor)
        self.treeWidget.currentItemChanged.connect(self.close_editor)
        self.treeWidget.itemChanged.connect(self.close_editor)
        self.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.openMenu)
        treeLayout = QHBoxLayout()
        treeLayout.addWidget(self.treeWidget)
        layout.addLayout(treeLayout)

        ''' Populate QTreeWidget '''
        root_label = list(self.tree.keys())[0]
        root = QTreeWidgetItem([root_label, ''])
        self.treeWidget.insertTopLevelItems(0, [root])
        self._generateTree(self.tree[root_label], root)

        ''' Prepare initial GUI state '''
        self.get_state()
        self.expand(0)
        self.expand(1)

        ''' Create optimizer layout '''
        optimizerLayout = QVBoxLayout()
        optimizerLayout.addWidget(QLabel('Optimizer'))
        self.algorithm_box = QComboBox()
        for item in self.control.optimizer.list_algorithms():
            self.algorithm_box.addItem(item)
        optimizerLayout.addWidget(self.algorithm_box)
        self.algorithm_box.currentTextChanged.connect(self.update_algorithm)
        self.params_edit = QTextEdit('')
        optimizerLayout.addWidget(self.params_edit)
        self.update_algorithm()

        self.cost_box = QComboBox()
        for item in self.control.list_costs():
            self.cost_box.addItem(item)
        optimizerLayout.addWidget(self.cost_box)

        self.optimizer_button = QPushButton('Go!')
        self.optimizer_button.clicked.connect(self.start_optimizer)
        optimizerLayout.addWidget(self.optimizer_button)
        layout.addLayout(optimizerLayout)

        ''' Ensure that only Inputs are selectable '''
        for item in self.get_all_items():
            if self.get_layer(item) != 2:
                item.setFlags(Qt.ItemIsEnabled)

    def close_editor(self):
        ''' Send actuate command and disable editing after the user presses return or clicks another node. '''
        try:
            if self.lastItem != self.currentItem:
                self.lastItem = self.currentItem
                self.currentItem = self.treeWidget.currentItem()
                self.treeWidget.closePersistentEditor(self.lastItem, 1)

                input = self.lastItem.text(0)
                device = self.lastItem.parent().text(0)
                key = device + '.' + input
                value = self.lastItem.text(1)
                state = {key: float(value)}
                self.control.actuate(state)
        except AttributeError:
            pass

    def expand(self, layer):
        ''' Expand all nodes in a given layer. '''
        items = self.get_all_items()
        items = [x for x in items if self.get_layer(x)==layer]
        for item in items:
            item.setExpanded(True)

    def _generateTree(self, children, parent):
        ''' Recursively add nodes to build the full network. '''
        for child in sorted(children):
            child_item = QTreeWidgetItem([child])
            parent.addChild(child_item)

            if isinstance(children, dict):
                self._generateTree(children[child], child_item)

    def get_all_items(self):
        """Returns all QTreeWidgetItems in the given QTreeWidget."""
        all_items = []
        for i in range(self.treeWidget.topLevelItemCount()):
            top_item = self.treeWidget.topLevelItem(i)
            all_items.extend(self.get_subtree_nodes(top_item))
        return all_items

    def get_input(self, full_name):
        ''' Return input item corresponding to a full_name. '''
        device_name = full_name.split('.')[0]
        input_name = full_name.split('.')[1]
        inputs = self.treeWidget.findItems(input_name, Qt.MatchExactly|Qt.MatchRecursive, 0)
        for input in inputs:
            if input.parent().text(0) == device_name:
                return input

    def get_items_on_level(self, level):
        all_items = self.get_all_items()

    def get_layer(self, item):
        ''' Get the layer in which an item resides. '''
        layer = 0
        parent = 0
        while item is not None:
            item = item.parent()
            layer +=1
        return layer-1

    def get_subtree_nodes(self, item):
        """Returns all QTreeWidgetItems in the subtree rooted at the given node."""
        nodes = []
        nodes.append(item)
        for i in range(item.childCount()):
            nodes.extend(self.get_subtree_nodes(item.child(i)))
        return nodes

    def get_state(self):
        ''' Read Control node state and update GUI. '''
        for key in self.control.state:
            self.get_input(key).setText(1, '%.2f'%self.control.state[key])

    def open_editor(self):
        ''' Allow the currently-selected node to be edited. '''
        self.currentItem = self.treeWidget.currentItem()
        col = self.treeWidget.currentIndex().column()
        if col == 1:
            self.treeWidget.openPersistentEditor(self.treeWidget.currentItem(), col)

    def start_optimizer(self):
        ''' Call chosen optimization routine with user-selected cost function and parameters '''
        func = getattr(self.control.optimizer, self.algorithm_box.currentText())
        params = self.params_edit.toPlainText().replace('\n','').replace("'", '"')
        print(params)
        params = json.loads(params)
        cost = getattr(self.control, self.cost_box.currentText())
        state = self.get_selected_state()
        if state == {}:
            print('Please select at least one Input node for optimization.')
        else:
            points, cost = func(state, cost, params)

    def update_algorithm(self):
        f = getattr(Optimizer, self.algorithm_box.currentText())
        ''' Read default params dict from source code and insert in self.params_edit. '''
        args = inspect.signature(f).parameters
        args = list(args.items())
        arguments = []
        for a in args:
            name = a[0]
            default = str(a[1])
            if default == name:
                default = 'Enter'
            else:
                default = default.split('=')[1]
                default = default.replace('{', '{\n')
                default = default.replace(',', ',\n')
                default = default.replace('}', '\n}')
                self.params_edit.setText(default)















    def openMenu(self, pos):
        level = self.get_selected_level()
        globalPos = self.mapToGlobal(pos)
        menu = QMenu()

        # if level == 0:
        #     optimize_action = QAction('Optimize', self)
        #     optimize_action.triggered.connect(self.optimizerWindow.show)
        #     menu.addAction(optimize_action)


        selectedItem = menu.exec_(globalPos)

    def get_selected_level(self):
        ''' Return the level of the currently selected item. '''
        indexes = self.treeWidget.selectedIndexes()
        level = 0
        index = indexes[0]
        while index.parent().isValid():
            index = index.parent()
            level += 1
        return level



    def get_selected_state(self):
        ''' Build a substate from all currently selected items. '''
        indexes = self.treeWidget.selectedIndexes()
        state = {}
        for i in indexes:
            if i.column() == 0:
                full_name = i.parent().data() + '.' + i.data()
                state[full_name] = float(i.sibling(i.row(), 1).data())
        return state
