#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import types
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
        QGroupBox, QHBoxLayout, QLabel, QLineEdit, QTreeView, QPushButton, QTableView,QVBoxLayout,
        QWidget, QMenu, QAction, QTreeWidget, QTreeWidgetItem)
from PyQt5.QtCore import *
from emergent.gui.elements.Optimizer import OptimizerWindow
import functools

class MainFrame(QWidget):
    def __init__(self, tree, control):
        QWidget.__init__(self)
        self.setWindowTitle('EMERGENT')
        with open('../../gui/stylesheet.txt',"r") as file:
            self.setStyleSheet(file.read())

        self.control = control
        self.tree = tree
        self.optimizerWindow = OptimizerWindow(self.control)

        self.currentItem = None
        self.lastItem = None

        self.treeWidget = QTreeWidget()
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

        layout = QHBoxLayout(self)
        layout.addWidget(self.treeWidget)

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
        all_items = get_all_items()

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
            self.get_input(key).setText(1, str(self.control.state[key]))

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
