#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
import sys
import types
from PyQt5.QtWidgets import (QAbstractItemView,QTreeView, QVBoxLayout,
        QMenu, QAction, QTreeWidget, QTreeWidgetItem)
from PyQt5.QtCore import *
import json
from emergent.gui.elements import ExperimentLayout
from emergent.archetypes import Control, Device, Input
from emergent.signals import ActuateSignal, SettingsSignal
import functools

class NodeTree(QTreeWidget):
    def __init__(self, tree, controls, parent):
        super().__init__()
        self.tree = tree
        self.controls = controls
        self.parent = parent
        self.editorOpen = 0
        self.current_item = None
        self.last_item = None

        self.setSelectionMode(QAbstractItemView.MultiSelection)
        self.setColumnCount(4)
        self.setHeaderLabels(["Node", "Value", "Min", "Max"])
        self.header().resizeSection(1,60)
        self.customContextMenuRequested.connect(self.openMenu)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.itemDoubleClicked.connect(self.open_editor)
        self.itemSelectionChanged.connect(self.close_editor)
        self.itemSelectionChanged.connect(self.deselect_nonsiblings)

        ''' Populate tree '''
        root_labels = list(self.tree.keys())
        roots = []
        for r in root_labels:
            roots.append(NodeWidget([r, ''], self.controls[r], 0))
        self.insertTopLevelItems(0, roots)

        for i in range(len(root_labels)):
            self._generateTree(self.tree[root_labels[i]], roots[i])

        self.expand(0)
        self.expand(1)

        ''' Ensure that only Inputs are selectable '''
        for item in self.get_all_items():
            if item.level != 2:
                item.setFlags(Qt.ItemIsEnabled)

        ''' Prepare initial GUI state '''
        for item in self.get_all_items():
            if item.node.node_type == 'device':
                self.sync_inputs(item)

        self.setColumnWidth(0,200)
        for i in [1,2,3]:
            self.setColumnWidth(i,50)

    def _generateTree(self, children, parent, level = 1):
        ''' Recursively add nodes to build the full network. '''
        for child in sorted(children):
            object = parent.node.children[child]

            child_item = NodeWidget([child.replace('_',' ')], object, level)
            parent.addChild(child_item)

            if isinstance(children, dict):
                self._generateTree(children[child], child_item, level = level+1)

    def close_editor(self):
        ''' Disable editing after the user clicks another node. '''
        try:
            col = self.currentIndex().column()
            self.last_item = self.current_item
            self.current_item = self.currentItem()
            if self.editorOpen:
                self.last_item.setText(col,self.currentValue)
            self.closePersistentEditor(self.last_item, col)
            self.editorOpen = 0
        except AttributeError:
            pass

    def deselect_nonsiblings(self):
        ''' Deselects items who are not siblings with the current item. '''
        item = self.currentItem()
        for i in self.get_all_items():
            if i.parent() is not item.parent():
                i.setSelected(0)

    def expand(self, layer):
        ''' Expand all nodes in a given layer. '''
        items = self.get_all_items()
        items = [x for x in items if x.level==layer]
        for item in items:
            item.setExpanded(True)

    def get_all_items(self):
        """Returns all connected NodeWidgets."""
        all_items = []
        for i in range(self.topLevelItemCount()):
            top_item = self.topLevelItem(i)
            all_items.extend(self.get_subtree_nodes(top_item))
        return all_items

    def get_selected_control(self):
        ''' Returns a control node corresponding to the selected input node. '''
        item = self.selectedItems()[0]
        control_name = item.parent().parent().text(0)
        return self.controls[control_name]

    def get_selected_state(self):
        ''' Build a substate from all currently selected inputs. '''
        items = self.selectedItems()
        state = {}
        for i in items:
            input = i.node
            dev = input.parent
            if dev.name not in state:
                state[dev.name] = {}
            state[dev.name][input.name] = input.state

        return state

    def get_subtree_nodes(self, item):
        """Returns all NodeItems in the subtree rooted at the given node."""
        nodes = []
        nodes.append(item)
        for i in range(item.childCount()):
            nodes.extend(self.get_subtree_nodes(item.child(i)))
        return nodes

    def update_editor(self):
        ''' Send actuate command and disable editing after the user presses return or clicks another node. '''
        try:
            col = self.currentIndex().column()
            self.last_item = self.current_item
            self.current_item = self.currentItem()
            self.closePersistentEditor(self.last_item, col)
            self.editorOpen = 0
            input = self.last_item.text(0)
            device = self.last_item.parent().text(0)
            key = device + '.' + input
            value = self.current_item.text(col)

            control_name = self.current_item.parent().parent().text(0)
            control = self.controls[control_name]
            input = self.current_item.node.name
            device = self.current_item.node.parent.name
            if col == 1:
                state = {device:{input: float(value)}}
                control.actuate(state)
            elif col == 2:
                control.settings[device][input]['min'] = float(value)
            elif col == 3:
                control.settings[device][input]['max'] = float(value)

        except AttributeError:
            pass

    def keyPressEvent(self, event):
        if event.key() == 16777220:
            self.update_editor()

    def open_editor(self):
        ''' Allow the currently-selected node to be edited. '''
        self.current_item = self.currentItem()
        self.currentValue = self.current_item.text(1)
        col = self.currentIndex().column()
        if col > 0:
            self.openPersistentEditor(self.currentItem(), col)
            self.editorOpen = 1

    def openMenu(self, pos):
        item = self.itemAt(pos)
        globalPos = self.mapToGlobal(pos)
        menu = QMenu()
        actions = {}
        for option in item.node.options:
            actions[option] = QAction(option, self)
            func = item.node.options[option]
            actions[option].triggered.connect(func)
            menu.addAction(actions[option])

        selectedItem = menu.exec_(globalPos)

    def sync_inputs(self, dev):
        ''' Switches from primary to secondary inputs for the passed in device item.
        '''
        for input in dev.node.children.values():
            input.leaf.setHidden(0)
            input.leaf.setText(1,str(input.state))

class NodeWidget(QTreeWidgetItem):
    def __init__(self, name, node, level):
        super().__init__(name)
        self.node = node
        self.level = level
        self.node.leaf = self
        self.root = self.get_root()

        if self.node.node_type == 'device':
            self.node.create_signal.connect(self.onCreateSignal)
            self.node.remove_signal.connect(self.onRemoveSignal)

        elif self.node.node_type == 'input':
            self.node.actuate_signal.connect(self.updateStateText)
            self.node.settings_signal.connect(self.updateSettingsText)

            name = self.node.name
            device = self.node.parent.name
            self.setText(2, str(self.root.settings[device][name]['min']))
            self.setText(3,str(self.root.settings[device][name]['max']))

    def __repr__(self):
        try:
            full_name = self.node.parent.name + '.' + self.node.name
            return full_name
        except AttributeError:
            return self.node.name

    def get_root(self):
        root = self.node
        while True:
            try:
                root = root.parent
            except AttributeError:
                return root

    def updateStateText(self, state):
        self.setText(1, str('%.2f'%state))

    def onCreateSignal(self, d):
        if self.node == d['device']:
            child_item = NodeWidget([d['input']], d['device'].children[d['input']], self.level+1)
            self.addChild(child_item)

    def onRemoveSignal(self, d):
        if self.node == d['device']:
            child_item = self.node.children[d['input']].leaf
            self.removeChild(child_item)

    def updateSettingsText(self, d):
        self.setText(2, str('%.2f'%float(d['min'])))
        self.setText(3, str('%.2f'%float(d['max'])))
