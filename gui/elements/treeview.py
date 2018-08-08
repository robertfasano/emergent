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
from archetypes.optimizer import Optimizer
from gui.elements.optimizer import OptimizerLayout
from archetypes.node import Control, Device, Input
import functools

class MyTreeWidget(QTreeWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def keyPressEvent(self, event):
        if event.key() == 16777220:
            self.parent.update_editor()

class MyTreeWidgetItem(QTreeWidgetItem):
    def __init__(self, name, node, level):
        super().__init__(name)
        self.node = node
        self.level = level
        self.node.leaf = self
        self.root = self.get_root()

        if self.node.node_type == 'device':
            self.inputs = 'secondary'

    def __repr__(self):
        try:
            return self.node.full_name
        except AttributeError:
            return self.node.name

    def get_root(self):
        root = self.node
        while True:
            try:
                root = root.parent
            except AttributeError:
                return root

class TreeLayout(QHBoxLayout):
    def __init__(self, tree, controls, window):
        super().__init__()

        self.controls = controls
        for c in self.controls.values():
            c.window = self
        self.window = window
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
        self.treeWidget.itemSelectionChanged.connect(self.close_editor)
        self.treeWidget.itemSelectionChanged.connect(self.deselect_nonsiblings)
        self.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.openMenu)
        self.addWidget(self.treeWidget)

        ''' Populate QTreeWidget '''
        root_labels = list(self.tree.keys())
        roots = []
        for r in root_labels:
            roots.append(MyTreeWidgetItem([r, ''], self.controls[r], 0))
        self.treeWidget.insertTopLevelItems(0, roots)

        for i in range(len(root_labels)):
            self._generateTree(self.tree[root_labels[i]], roots[i])

        ''' Prepare initial GUI state '''
        for control in controls.keys():
            self.update_state(control)
        self.expand(0)
        self.expand(1)
        for item in self.get_all_items():
            if item.node.node_type == 'device':
                self.toggle_inputs(item)

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

    def expand(self, layer):
        ''' Expand all nodes in a given layer. '''
        items = self.get_all_items()
        items = [x for x in items if x.level==layer]
        for item in items:
            item.setExpanded(True)

    def _generateTree(self, children, parent, level = 1):
        ''' Recursively add nodes to build the full network. '''
        for child in sorted(children):
            object = parent.node.children[child]

            child_item = MyTreeWidgetItem([child], object, level)
            parent.addChild(child_item)

            if isinstance(children, dict):
                self._generateTree(children[child], child_item, level = level+1)

    def toggle_inputs(self, dev):
        ''' Switches from primary to secondary inputs for the passed in device item.
        '''
        type = 'primary'
        if dev.inputs == 'primary':
            type = 'secondary'
        old_type = dev.inputs
        dev.inputs = type
        dev.node.use_inputs(type)
        for input in dev.node.children.values():
            if input.type == type:
                input.leaf.setHidden(0)
                input.leaf.setText(1,str(input.state))

        for input in dev.node.children.values():
            if input.type == old_type:
                input.leaf.setHidden(1)

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

    def get_selected_control(self):
        ''' Returns a control node corresponding to the selected input node. '''
        ''' WARNING: will cause unpredicted behavior if nodes across controls are selected '''
        item = self.treeWidget.selectedItems()[0]
        control_name = item.parent().parent().text(0)
        return self.controls[control_name]

    def get_selected_level(self):
        ''' Return the level of the currently selected item. '''
        item = self.treeWidget.selectedItems()[0]
        return item.level

    def get_selected_state(self):
        ''' Build a substate from all currently selected inputs. '''
        items = self.treeWidget.selectedItems()
        state = {}
        for i in items:
            input = i.node
            dev = input.parent
            state[dev.name + '.' + input.name] = input.state

        return state

    def get_subtree_nodes(self, item):
        """Returns all QTreeWidgetItems in the subtree rooted at the given node."""
        nodes = []
        nodes.append(item)
        for i in range(item.childCount()):
            nodes.extend(self.get_subtree_nodes(item.child(i)))
        return nodes

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

    def deselect_nonsiblings(self):
        ''' Deselects items who are not siblings with the current item. '''
        item = self.treeWidget.currentItem()
        for i in self.get_all_items():
            if i.parent() is not item.parent():
                i.setSelected(0)

    def update_state(self, control):
        ''' Read Control node state and update GUI. '''
        for key in self.controls[control].state:
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
        item = self.treeWidget.itemAt(pos)
        globalPos = self.treeWidget.mapToGlobal(pos)
        menu = QMenu()

        if item.node.node_type == 'device':
            if item.node.secondary_inputs > 0:
                other_input_type = {'secondary':'primary', 'primary':'secondary'}[item.inputs]
                hide_secondary_inputs_action = QAction('Show %s inputs'%other_input_type, self)
                hide_secondary_inputs_action.triggered.connect(functools.partial(self.toggle_inputs,self.treeWidget.currentItem()))
                menu.addAction(hide_secondary_inputs_action)

        selectedItem = menu.exec_(globalPos)
