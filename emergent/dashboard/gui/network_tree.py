''' The NetworkPanel displays a custom implementation of a QTreeWidget with the
    following features:

    * Each node is linked to its corresponding "leaf".
    * Local or remote actuate() calls can be issued by changing a value and pressing enter.
    * The NodeTree.generate(network) method examines the passed network; any new Hubs are added, while existing hubs have their state display updated.
    * The Hub.actuate() method emits a signal which updates leaves corresponding to actuated nodes.
    * Undo/redo buttons allow Thing/Hub states to be recalled from a buffer.
'''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QAbstractItemView, QVBoxLayout,
        QMenu, QAction, QTreeWidget, QTreeWidgetItem, QHeaderView, QPushButton)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import *
from emergent.utilities.containers import State

class NodeTree(QTreeWidget):
    def __init__(self, network, dashboard):
        super().__init__()
        self.network = network
        self.dashboard = dashboard
        self.editorOpen = 0
        self.current_item = None
        self.last_item = None
        self.setSelectionMode(QAbstractItemView.MultiSelection)
        self.setColumnCount(6)
        # self.setHeaderLabels(["Node", "Value", "Min", "Max"])
        header_item = QTreeWidgetItem(['Node', 'Value', 'Min', 'Max'])
        self.setHeaderItem(header_item)
        # self.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        # for i in range(1,4):
        #     self.header().setSectionResizeMode(i, QHeaderView.Stretch)
        # for i in range(4, 6):
        #     self.header().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        # self.header().setStretchLastSection(False)
        #
        # self.header().setFixedHeight(25)
        #
        # self.customContextMenuRequested.connect(self.openMenu)
        # self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.itemDoubleClicked.connect(self.open_editor)
        self.itemSelectionChanged.connect(self.close_editor)

        ''' Populate tree '''
        self.generate(self.network)
        self.setColumnWidth(0,200)
        for i in [1,2,3]:
            self.setColumnWidth(i,50)

    def actuate(self, hub, state):
        hub_item = self.get_hub(hub)
        for thing_name in state:
            thing = self.get_thing(hub, thing_name)
            for input in state[thing_name]:
                self.get_input(hub, thing_name, input).state_signal.emit(state[thing_name][input])

    def set_settings(self, hub, settings):
        hub_item = self.get_hub(hub)
        for thing_name in settings:
            thing = self.get_thing(hub, thing_name)
            for input in settings[thing_name]:
                leaf = self.get_input(hub, thing_name, input)
                leaf.min_signal.emit(settings[thing_name][input]['min'])
                leaf.max_signal.emit(settings[thing_name][input]['max'])

    def add_node(self, parent, name):
        leaf = QTreeWidgetItem([name])
        parent.addChild(leaf)
        return leaf

    def expand(self):
        ''' Expand all nodes in a given layer. '''
        items = self.get_all_items()
        for item in items:
            item.setExpanded(True)

    def generate(self, network, settings = None):
        ''' Adds the passed network to the tree. If any hubs are already registered with the tree,
            instead updates their state based on the passed network. '''
        for hub in network:
            if self.get_hub(hub) is not None:
                self.actuate(hub, network[hub])
                settings = self.dashboard.p2p.send({'op': 'get', 'target': 'settings'})['value']
                self.set_settings(hub, settings[hub])
                self.dashboard.app.processEvents()
                continue
            root = QTreeWidgetItem([hub])
            self.insertTopLevelItems(self.topLevelItemCount(), [root])
            for thing in network[hub]:
                branch = self.add_node(root, thing)
                for input in network[hub][thing]:
                    leaf = InputWidget(input)
                    branch.addChild(leaf)
            self.actuate(hub, network[hub])       # update tree to current hub state
            settings = self.dashboard.p2p.send({'op': 'get', 'target': 'settings'})['value']
            self.set_settings(hub, settings[hub])
            self.expand()
        self.dashboard.app.processEvents()


    ''' Logistics methods '''
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
            state[thing.name][input.display_name] = input.state

        return state

    def get_subtree_nodes(self, item):
        """Returns all NodeItems in the subtree rooted at the given node."""
        nodes = []
        nodes.append(item)
        for i in range(item.childCount()):
            nodes.extend(self.get_subtree_nodes(item.child(i)))
        return nodes

    ''' User interaction methods '''
    def open_editor(self):
        ''' Allow the currently-selected node to be edited. '''
        self.current_item = self.currentItem()
        self.currentValue = self.current_item.text(1)
        col = self.currentIndex().column()
        if col == 0:
            return
        if col in [1,2,3]:
            self.openPersistentEditor(self.currentItem(), col)
            self.editorOpen = 1

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
            hub = self.last_item.parent().parent().text(0)

            key = thing + '.' + input
            value = self.current_item.text(col)

            hub_name = self.current_item.parent().parent().text(0)
            thing_name = self.current_item.parent().text(0)
            input_name = self.current_item.text(0)

            if col == 1:
                state = {thing_name:{input_name: float(value)}}
                # self.dashboard.p2p.sender.actuate({hub_name: state})
                self.dashboard.p2p.send({'op': 'set', 'target': 'state', 'value': {hub_name: state}})
            elif col in [2,3]:
                print('No settings functionality yet')
                return
                # d = {'min': float(self.current_item.text(2)),
                #      'max': float(self.current_item.text(3))}
                # state = {hub: {thing: {input: d}}}
                # self.dashboard.client.set_range(state)

        except AttributeError as e:
            print(e)

    def keyPressEvent(self, event):
        if event.key() == 16777220:
            self.update_editor()

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

from emergent.utilities.signals import FloatSignal

class InputWidget(QTreeWidgetItem):
    def __init__(self, name):
        super().__init__([name])
        self.name = name
        self.state_signal = FloatSignal()
        self.state_signal.connect(self.updateStateText)
        self.min_signal = FloatSignal()
        self.min_signal.connect(self.updateMinText)
        self.max_signal = FloatSignal()
        self.max_signal.connect(self.updateMaxText)

    def updateStateText(self, state):
        self.setText(1, str('%.2f'%state))

    def updateMinText(self, state):
        self.setText(2, str('%.2f'%state))

    def updateMaxText(self, state):
        self.setText(3, str('%.2f'%state))
