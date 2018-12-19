#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
import sys
import types
from PyQt5.QtWidgets import (QWidget, QAbstractItemView,QTreeView, QVBoxLayout,
        QMenu, QAction, QTreeWidget, QTreeWidgetItem, QHeaderView, QPushButton, QHBoxLayout)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import *
import json
from emergent.gui.elements import ExperimentLayout
from emergent.modules import Hub, Thing, Input, State
from emergent.signals import ActuateSignal
import functools
import logging as log

class UndoButton(QWidget):
    def __init__(self, item, buffer, signal):
        QWidget.__init__(self)
        self.buffer = buffer
        self.item = item
        self.layout = QVBoxLayout(self)
        self.button = QPushButton()
        self.button.clicked.connect(self.undo)
        self.layout.addWidget(self.button)
        self.button.setStyleSheet("background-color: rgba(255, 255, 255, 0);")

        icon = QIcon()
        icon.addPixmap(QPixmap('gui/media/Material/undo.svg'),QIcon.Normal,QIcon.On)
        icon.addPixmap(QPixmap('gui/media/Material/blank.svg'),QIcon.Normal,QIcon.Off)
        self.button.setIcon(icon)
        self.button.setCheckable(True)
        self.show()
        signal.connect(self.show)
    # def enterEvent(self, event, initial = True):
    #     self.show()
    #
    # def leaveEvent(self, event):
    #     self.button.setChecked(False)

    def show(self):
        self.button.setChecked(self.buffer.index > -len(self.buffer))

    def undo(self):
        self.buffer.undo()
        self.show()
        self.item.redo_button.show()

    def sizeHint(self):
        return QSize(50, 28)

class RedoButton(QWidget):
    def __init__(self, item, buffer, signal):
        QWidget.__init__(self)
        self.item = item
        self.buffer = buffer
        self.layout = QVBoxLayout(self)
        self.button = QPushButton()
        self.button.clicked.connect(self.redo)
        self.layout.addWidget(self.button)
        self.button.setStyleSheet("background-color: rgba(255, 255, 255, 0);")

        icon = QIcon()
        icon.addPixmap(QPixmap('gui/media/Material/redo.svg'),QIcon.Normal,QIcon.On)
        icon.addPixmap(QPixmap('gui/media/Material/blank.svg'),QIcon.Normal,QIcon.Off)
        self.button.setIcon(icon)
        self.button.setCheckable(True)
        self.show()
        signal.connect(self.show)
    # def enterEvent(self, event, initial = True):
    #     self.show()
    #
    # def leaveEvent(self, event):
    #     self.button.setChecked(False)

    def redo(self):
        self.buffer.redo()
        self.show()
        self.item.undo_button.show()

    def show(self):
        self.button.setChecked(self.buffer.index != -1)

    def sizeHint(self):
        return QSize(50, 28)

class NodeTree(QTreeWidget):
    def __init__(self, network, parent):
        super().__init__()
        self.network = network
        self.network.tree = self
        self.parent = parent
        self.editorOpen = 0
        self.current_item = None
        self.last_item = None

        self.setSelectionMode(QAbstractItemView.MultiSelection)
        self.setColumnCount(6)
        # self.setHeaderLabels(["Node", "Value", "Min", "Max"])
        header_item = QTreeWidgetItem(['Node', 'Value', 'Min', 'Max', '', ''])
        self.setHeaderItem(header_item)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for i in range(1,4):
            self.header().setSectionResizeMode(i, QHeaderView.Stretch)
        for i in range(4, 6):
            self.header().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.header().setStretchLastSection(False)

        self.header().setFixedHeight(20)
        # self.header().setStyleSheet('::section{border: 0px solid; border-right: 0px; border-left: 0px; font-weight: normal}')

        self.customContextMenuRequested.connect(self.openMenu)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.itemDoubleClicked.connect(self.open_editor)
        self.itemSelectionChanged.connect(self.close_editor)
        self.itemSelectionChanged.connect(self.deselect_nonsiblings)

        ''' Populate tree '''
        self.generate(self.network)

        ''' Ensure that only Inputs are selectable '''
        for item in self.get_all_items():
            if item.node.node_type != 'input':
                item.setFlags(Qt.ItemIsEnabled)

        ''' Prepare initial GUI state '''
        for c in self.network.hubs:
            node = self.get_hub(c).node
            self.actuate(c, node.state)

        self.setColumnWidth(0,200)
        for i in [1,2,3]:
            self.setColumnWidth(i,50)

        ''' Add undo/redo buttons '''
        for item in self.get_all_items():
            if item.node.node_type != 'input':
                item.add_buffer_buttons()

    def actuate(self, hub, state):
        hub_item = self.get_hub(hub)
        for thing in state:
            for input in state[thing]:
                self.get_input(hub, thing, input).updateStateText(state[thing][input])

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

    def expand(self, node_type):
        ''' Expand all nodes in a given layer. '''
        items = self.get_all_items()
        items = [x for x in items if x.node.node_type==node_type]
        for item in items:
            item.setExpanded(True)

    def generate(self, network):
        ''' Adds the passed network to the tree. If any hubs are already registered with the tree,
            instead updates their state based on the past network. '''
        for hub in network.hubs.values():
            if self.get_hub(hub.name) is not None:
                self.actuate(hub.name, hub.state)
                continue
            root = NodeWidget(hub)
            self.insertTopLevelItems(0, [root])
            for thing in hub.children.values():
                branch = NodeWidget(thing)
                root.addChild(branch)
                for input in thing.children.values():
                    leaf = NodeWidget(input)
                    branch.addChild(leaf)
            self.actuate(hub.name, hub.state)       # update tree to current hub state
            self.expand('hub')
            self.expand('thing')

    # def generate(self, network):
    #     ''' Adds the passed network to the tree. If any hubs are already registered with the tree,
    #         instead updates their state based on the past network. '''
    #     for hub in network:
    #         if self.get_hub(hub) is not None:
    #             self.actuate(hub, network[hub])
    #             continue
    #         root = NodeWidget(hub)
    #         self.insertTopLevelItems(0, [root])
    #         for thing in network[hub]:
    #             branch = NodeWidget(thing)
    #             root.addChild(branch)
    #             for input in network[hub][thing]:
    #                 leaf = NodeWidget(input)
    #                 branch.addChild(leaf)
    #         self.actuate(hub, network[hub])       # update tree to current hub state
    #         self.expand('hub')
    #         self.expand('thing')

    def get_all_items(self):
        """Returns all connected NodeWidgets."""
        all_items = []
        for i in range(self.topLevelItemCount()):
            top_item = self.topLevelItem(i)
            all_items.extend(self.get_subtree_nodes(top_item))
        return all_items

    def get_hub(self, hub):
        ''' Return a QTreeWidgetItem with the given hub name '''
        for i in range(self.topLevelItemCount()):
            if self.topLevelItem(i).text(0) == hub:
                return self.topLevelItem(i)

    def get_thing(self, hub, thing):
        hub_item = self.get_hub(hub)
        for i in range(hub_item.childCount()):
            if hub_item.child(i).text(0) == thing:
                return hub_item.child(i)

    def get_input(self, hub, thing, input):
        hub_item = self.get_hub(hub)
        thing_item = self.get_thing(hub, thing)
        for i in range(thing_item.childCount()):
            if thing_item.child(i).text(0) == input:
                return thing_item.child(i)

    def get_selected_hub(self):
        ''' Returns a hub node corresponding to the selected input node. '''
        item = self.selectedItems()[0]
        hub_name = item.parent().parent().text(0)
        hub = self.network.hubs[hub_name]
        
        return hub

    def get_selected_state(self):
        ''' Build a substate from all currently selected inputs. '''
        items = self.selectedItems()
        state = State()
        for i in items:
            input = i.node
            thing = input.parent
            if thing.name not in state:
                state[thing.name] = {}
            state[thing.name][input.name] = input.state

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
            thing = self.last_item.parent().text(0)
            key = thing + '.' + input
            value = self.current_item.text(col)

            hub_name = self.current_item.parent().parent().text(0)
            hub = self.current_item.node.parent.parent
            # hub = self.network.hubs[hub_name]
            input = self.current_item.node.name
            thing = self.current_item.node.parent.name
            if col == 1:
                state = {thing:{input: float(value)}}
                if hub.addr == self.network.addr:
                    hub.actuate(state)
                else:
                    self.network.clients[hub.addr].actuate({hub.name: state})
            elif col == 2:
                hub.settings[thing][input]['min'] = float(value)
            elif col == 3:
                hub.settings[thing][input]['max'] = float(value)

        except AttributeError as e:
            print(e)

    def keyPressEvent(self, event):
        if event.key() == 16777220:
            self.update_editor()

    def open_editor(self):
        ''' Allow the currently-selected node to be edited. '''
        self.current_item = self.currentItem()
        self.currentValue = self.current_item.text(1)
        col = self.currentIndex().column()
        if col in [1,2,3]:
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

class NodeWidget(QTreeWidgetItem):
    def __init__(self, node):
        super().__init__([node.name])
        self.node = node
        self.root = self.get_root()

        if self.node.node_type == 'hub' and hasattr(self.node, 'signal'):
            self.node.signal.connect(self.onActuateSignal)
        # if self.node.node_type == 'thing':
        #     self.node.create_signal.connect(self.onCreateSignal)
        #     self.node.remove_signal.connect(self.onRemoveSignal)
        elif self.node.node_type == 'input':
            name = self.node.name
            thing = self.node.parent.name
            self.setText(2, str(self.root.settings[thing][name]['min']))
            self.setText(3,str(self.root.settings[thing][name]['max']))

    def add_buffer_buttons(self):
        if not (hasattr(self.node, 'signal') or hasattr(self.node, 'process_signal')):
            return
        if self.node.node_type == 'thing':
            signal = self.node.signal
            buffer = self.node.buffer
        else:
            signal = self.node.process_signal
            buffer = self.node.macro_buffer
        self.undo_button = UndoButton(self, buffer, signal)
        self.treeWidget().setItemWidget(self, 4, self.undo_button)

        self.redo_button = RedoButton(self, buffer, signal)
        self.treeWidget().setItemWidget(self, 5, self.redo_button)

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

    def onActuateSignal(self, state):
        self.treeWidget().actuate(self.node.name, state)

    def updateStateText(self, state):
        self.setText(1, str('%.2f'%state))

    # def onCreateSignal(self, d):
    #     if self.node == d['thing']:
    #         child_item = NodeWidget([d['input']], d['thing'].children[d['input']])
    #         self.addChild(child_item)
    #
    # def onRemoveSignal(self, d):
    #     if self.node == d['thing']:
    #         child_item = self.node.children[d['input']].leaf
    #         self.removeChild(child_item)
