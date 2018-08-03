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
from emergent.gui.elements.Optimizer import OptimizerWindow
from emergent.archetypes.Optimizer import Optimizer
import json

class MainFrame(QWidget):
    def __init__(self, tree, control):
        QWidget.__init__(self)
        self.setWindowTitle('EMERGENT')
        with open('../../gui/stylesheet.txt',"r") as file:
            self.setStyleSheet(file.read())

        self.control = control
        self.control.window = self
        self.tree = tree
        self.optimizerWindow = OptimizerWindow(self.control)

        self.currentItem = None
        self.lastItem = None

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

        root_label = list(self.tree.keys())[0]
        root = QTreeWidgetItem([root_label, ''])
        self.treeWidget.insertTopLevelItems(0, [root])
        self._generateTree(self.tree[root_label], root)
        self.get_state()
        self.expand(0)
        self.expand(1)

        treeLayout = QHBoxLayout()
        treeLayout.addWidget(self.treeWidget)

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

        ''' Ensure that only Inputs are selectable '''
        for item in self.get_all_items():
            if self.get_layer(item) != 2:
                item.setFlags(Qt.ItemIsEnabled)


        layout= QHBoxLayout(self)


        layout.addLayout(treeLayout)
        layout.addLayout(optimizerLayout)

    def start_optimizer(self):
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
        doc = inspect.getdoc(f)
        # self.algorithm_label.setText(doc)
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

    def expand(self, layer):
        items = self.get_all_items()
        items = [x for x in items if self.get_layer(x)==layer]
        for item in items:
            item.setExpanded(True)


    def open_editor(self):
        self.currentItem = self.treeWidget.currentItem()
        col = self.treeWidget.currentIndex().column()
        if col == 1:
            self.treeWidget.openPersistentEditor(self.treeWidget.currentItem(), col)

    def close_editor(self):
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


    def get_device(self, name):
        return self.treeWidget.findItems(name, Qt.MatchExactly|Qt.MatchRecursive, 0)[0]

    def get_input(self, full_name):
        device_name = full_name.split('.')[0]
        input_name = full_name.split('.')[1]
        inputs = self.treeWidget.findItems(input_name, Qt.MatchExactly|Qt.MatchRecursive, 0)
        for input in inputs:
            if input.parent().text(0) == device_name:
                return input

    def get_items_on_level(self, level):
        all_items = self.get_all_items()

    def get_subtree_nodes(self, item):
        """Returns all QTreeWidgetItems in the subtree rooted at the given node."""
        nodes = []
        nodes.append(item)
        for i in range(item.childCount()):
            nodes.extend(self.get_subtree_nodes(item.child(i)))
        return nodes

    def get_all_items(self):
        """Returns all QTreeWidgetItems in the given QTreeWidget."""
        all_items = []
        for i in range(self.treeWidget.topLevelItemCount()):
            top_item = self.treeWidget.topLevelItem(i)
            all_items.extend(self.get_subtree_nodes(top_item))
        return all_items

    def get_state(self):
        for key in self.control.state:
            self.get_input(key).setText(1, '%.2f'%self.control.state[key])

    def _generateTree(self, children, parent):
        for child in sorted(children):
            child_item = QTreeWidgetItem([child])
            parent.addChild(child_item)

            if isinstance(children, dict):
                self._generateTree(children[child], child_item)

    def get_layer(self, item):
        layer = 0
        parent = 0
        while item is not None:
            item = item.parent()
            layer +=1
        return layer-1

    def openMenu(self, pos):
        level = self.get_selected_level()
        globalPos = self.mapToGlobal(pos)
        menu = QMenu()

        if level == 0:
            optimize_action = QAction('Optimize', self)
            optimize_action.triggered.connect(self.optimizerWindow.show)
            menu.addAction(optimize_action)


        selectedItem = menu.exec_(globalPos)

    def get_selected_level(self):
        indexes = self.treeWidget.selectedIndexes()
        level = 0
        index = indexes[0]
        while index.parent().isValid():
            index = index.parent()
            level += 1
        return level

    def get_selected_key(self):
        item = self.treeWidget.currentItem()
        input = item.text(0)
        device = item.parent().text(0)
        key = device + '.' + input
        print(key)
        return key

    def get_selected_keys(self):
        indexes = self.treeWidget.selectedIndexes()
        keys = []
        for i in indexes:
            if i.column() == 0:
                full_name = i.parent().data() + '.' + i.data()
                keys.append(full_name)
        return keys

    def get_selected_state(self):
        indexes = self.treeWidget.selectedIndexes()
        state = {}
        for i in indexes:
            if i.column() == 0:
                full_name = i.parent().data() + '.' + i.data()
                state[full_name] = float(i.sibling(i.row(), 1).data())
        return state
