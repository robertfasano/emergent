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

class MyTreeWidget(QTreeWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def keyPressEvent(self, event):
        if event.key() == 16777220:
            self.parent.update_editor()

class TreeLayout(QHBoxLayout):
    def __init__(self, tree, controls):
        super().__init__()

        self.controls = controls
        # self.controls = controls
        # for c in self.controls:
        #     c.window = self
        self.tree = tree

        self.editorOpen = 0
        self.currentItem = None
        self.lastItem = None

        ''' Create QTreeWidget '''
        self.treeWidget = MyTreeWidget(self)
        self.treeWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.treeWidget.setColumnCount(2)
        self.treeWidget.setHeaderLabels(["Node", "Value"])
        self.treeWidget.header().resizeSection(1,60)
        self.treeWidget.itemDoubleClicked.connect(self.open_editor)
        self.treeWidget.itemSelectionChanged.connect(self.close_editor, Qt.UniqueConnection)
        # self.treeWidget.itemChanged.connect(self.update_editor, Qt.UniqueConnection)
        #self.treeWidget.keyPressEvent.connect(self.update_editor, Qt.UniqueConnection)
        self.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.openMenu)
        self.addWidget(self.treeWidget)

        ''' Populate QTreeWidget '''
        root_labels = list(self.tree.keys())
        roots = []
        for r in root_labels:
            roots.append(QTreeWidgetItem([r, '']))
        self.treeWidget.insertTopLevelItems(0, roots)

        for i in range(len(root_labels)):
            self._generateTree(self.tree[root_labels[i]], roots[i])


        ''' Prepare initial GUI state '''
        for control in controls.keys():
            self.get_state(control)
        self.expand(0)
        self.expand(1)

    def close_editor(self):
        ''' Disable editing after the user clicks another node. '''
        try:

            self.lastItem = self.currentItem
            self.currentItem = self.treeWidget.currentItem()
            if self.editorOpen:
                self.lastItem.setText(1,self.currentValue)
            self.treeWidget.closePersistentEditor(self.lastItem, 1)
            self.editorOpen = 0
        except AttributeError:
            pass

    def update_editor(self):
        ''' Send actuate command and disable editing after the user presses return or clicks another node. '''
        try:
            self.lastItem = self.currentItem
            self.currentItem = self.treeWidget.currentItem()
            self.treeWidget.closePersistentEditor(self.lastItem, 1)
            self.editorOpen = 0
            input = self.lastItem.text(0)
            device = self.lastItem.parent().text(0)
            key = device + '.' + input
            value = self.currentItem.text(1)
            state = {key: float(value)}
            control = self.currentItem.parent().parent().text(0)
            self.controls[control].actuate(state)
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

    def get_input_control(self, full_name):
        item = self.get_input(full_name)
        control = item.parent().parent().text(0)
        return getattr(__main__, control)

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
        items = []
        for i in all_items:
            if self.get_layer(i) == level:
                items.append(i)
        return items

    def get_layer(self, item):
        ''' Get the layer in which an item resides. '''
        layer = 0
        parent = 0
        while item is not None:
            item = item.parent()
            layer +=1
        return layer-1

    def get_selected_control(self):
        ''' Returns a control node corresponding to the selected input node. '''
        ''' WARNING: will cause unpredicted behavior if nodes across controls are selected '''
        item = self.treeWidget.selectedItems()[0]
        control_name = item.parent().parent().text(0)
        return self.controls[control_name]

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

    def get_subtree_nodes(self, item):
        """Returns all QTreeWidgetItems in the subtree rooted at the given node."""
        nodes = []
        nodes.append(item)
        for i in range(item.childCount()):
            nodes.extend(self.get_subtree_nodes(item.child(i)))
        return nodes

    def get_state(self, control):
        ''' Read Control node state and update GUI. '''
        for key in self.controls[control].state:
            print(key)
            print(self.get_input(key))
            self.get_input(key).setText(1, '%.2f'%self.controls[control].state[key])

    def open_editor(self):
        ''' Allow the currently-selected node to be edited. '''
        self.currentItem = self.treeWidget.currentItem()
        self.currentValue = self.currentItem.text(1)
        col = self.treeWidget.currentIndex().column()
        if col == 1:
            self.treeWidget.openPersistentEditor(self.treeWidget.currentItem(), col)
            self.editorOpen = 1
    def openMenu(self, pos):
        level = self.get_selected_level()
        globalPos = self.mapToGlobal(pos)
        menu = QMenu()

        # if level == 0:
        #     optimize_action = QAction('Optimize', self)
        #     optimize_action.triggered.connect(self.optimizerWindow.show)
        #     menu.addAction(optimize_action)


        selectedItem = menu.exec_(globalPos)
