''' The NetworkPanel displays a custom implementation of a QTreeWidget with the
    following features:

    * Each node is linked to its corresponding "leaf".
    * Local or remote actuate() calls can be issued by changing a value and pressing enter.
    * The NodeTree.generate(network) method examines the passed network; any new Hubs are added, while existing hubs have their state display updated.
    * The Hub.actuate() method emits a signal which updates leaves corresponding to actuated nodes.
    * Undo/redo buttons allow Device/Hub states to be recalled from a buffer.
'''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QAbstractItemView, QVBoxLayout,
        QMenu, QAction, QTreeWidget, QTreeWidgetItem, QHeaderView, QPushButton)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import *
from emergent.utilities.containers import State
from emergent.dashboard.structures.dict_menu import DictMenu
from functools import partial

class NodeTree(QTreeWidget):
    def __init__(self, dashboard):
        super().__init__()
        self.dashboard = dashboard
        self.objectName = 'NodeTree'
        self.editorOpen = 0
        self.current_item = None
        self.last_item = None
        self.locked = False
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
        self.customContextMenuRequested.connect(self.openMenu)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.itemDoubleClicked.connect(self.open_editor)
        self.itemSelectionChanged.connect(self.close_editor)
        self.itemSelectionChanged.connect(self.deselect_nonsiblings)

        ''' Populate tree '''
        self.set_state(self.dashboard.get('state'))
        range = self.dashboard.get('range')
        for hub in range:
            self.set_range(hub, range[hub])

        ''' Ensure that only Knobs are selectable '''
        for item in self.get_all_items():
            if item.node != 'knob':
                item.setFlags(Qt.ItemIsEnabled)

        self.setColumnWidth(0,200)
        for i in [1,2,3]:
            self.setColumnWidth(i,50)

        self.dashboard.actuate_signal.connect(self.set_state)
        self.dashboard.sequence_update_signal.connect(self.refresh)

    def lock(self):
        self.locked = not self.locked
        if self.locked:
            self.close_editor()
    def refresh(self):
        self.set_state(self.dashboard.get('state'))

    def actuate(self, hub, state):
        hub_item = self.get_hub(hub)
        for device_name in state:
            device = self.get_device(hub, device_name)
            for knob in state[device_name]:
                value = state[device_name][knob]
                if self.get_knob(hub, device_name, knob) is None:
                    leaf = KnobWidget(knob)
                    device.addChild(leaf)
                if value is not None:
                    self.get_knob(hub, device_name, knob).state_signal.emit(state[device_name][knob])

    def set_range(self, hub, settings):
        hub_item = self.get_hub(hub)
        for device_name in settings:
            device = self.get_device(hub, device_name)
            for knob in settings[device_name]:
                leaf = self.get_knob(hub, device_name, knob)
                min = settings[device_name][knob]['min']
                if min is not None:
                    leaf.min_signal.emit(min)
                max = settings[device_name][knob]['max']
                if max is not None:
                    leaf.max_signal.emit(max)

    def add_node(self, parent, name):
        leaf = QTreeWidgetItem([name])
        parent.addChild(leaf)
        return leaf

    def deselect_nonsiblings(self):
        ''' Deselects items who do not live under the same Hub as the
            current item. '''
        item = self.currentItem()
        for i in self.get_all_items():
            if i.node == 'knob':
                if i.parent().parent() is not item.parent().parent():
                    i.setSelected(0)

    def expand(self):
        ''' Expand all nodes in a given layer. '''
        items = self.get_all_items()
        for item in items:
            item.setExpanded(True)

    def set_state(self, network, settings = None):
        ''' Adds the passed network to the tree. If any hubs are already registered with the tree,
            instead updates their state based on the passed network. '''
        for hub in network:
            if self.get_hub(hub) is not None:
                self.actuate(hub, network[hub])
                continue
            root = HubWidget(hub)
            self.insertTopLevelItems(self.topLevelItemCount(), [root])
            for device in network[hub]:
                branch = DeviceWidget(device)
                root.addChild(branch)
                for knob in network[hub][device]:
                    leaf = KnobWidget(knob)
                    branch.addChild(leaf)
            self.actuate(hub, network[hub])       # update tree to current hub state
            self.expand()


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

    def get_device(self, hub, device):
        hub_item = self.get_hub(hub)
        for i in range(hub_item.childCount()):
            if hub_item.child(i).text(0) == device:
                return hub_item.child(i)

    def get_knob(self, hub, device, knob):
        hub_item = self.get_hub(hub)
        device_item = self.get_device(hub, device)
        for i in range(device_item.childCount()):
            if device_item.child(i).text(0) == knob:
                return device_item.child(i)

    def get_selected_hub(self):
        ''' Returns a hub node corresponding to the selected knob node. '''
        try:
            item = self.selectedItems()[0]
        except IndexError:
            return
        hub_name = item.parent().parent().text(0)

        return hub_name

    def get_selected_state(self):
        ''' Build a substate from all currently selected knobs. '''
        items = self.selectedItems()
        state = State()
        for i in items:
            knob_name = i.name
            device_name = i.parent().text(0)
            if device_name not in state:
                state[device_name] = {}
            state[device_name][knob_name] = float(i.text(1))

        return state

    def get_selected_range(self):
        ''' Build a range dict from all currently selected knobs. '''
        items = self.selectedItems()
        state = {}
        for i in items:
            knob_name = i.name
            device_name = i.parent().text(0)
            if device_name not in state:
                state[device_name] = {}
            state[device_name][knob_name] = {'min': float(i.text(2)),
                                            'max': float(i.text(3))}

        return state

    def get_state(self):
        ''' Returns a dict representating the state of the tree. '''
        all_items = []
        state = State()
        for i in range(self.topLevelItemCount()):
            hub_item = self.topLevelItem(i)
            state[hub_item.text(0)] = {}
            for j in range(hub_item.childCount()):
                device_item = hub_item.child(j)
                state[hub_item.text(0)][device_item.text(0)] = {}
                for k in range(device_item.childCount()):
                    knob_item = device_item.child(k)
                    state[hub_item.text(0)][device_item.text(0)][knob_item.text(0)] = knob_item.text(1)
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
        if self.locked:
            return
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
            knob = self.last_item.text(0)
            device = self.last_item.parent().text(0)
            hub = self.last_item.parent().parent().text(0)

            key = device + '.' + knob
            value = self.current_item.text(col)

            hub_name = self.current_item.parent().parent().text(0)
            device_name = self.current_item.parent().text(0)
            knob_name = self.current_item.text(0)

            if col == 1:
                state = {hub_name: {device_name:{knob_name: float(value)}}}
                self.dashboard.post('state', state)
                self.dashboard.actuate_signal.emit(state)
            elif col in [2,3]:
                qty = {2: 'min', 3: 'max'}[col]
                range = {hub_name: {device_name:{knob_name: {qty: float(value)}}}}
                self.dashboard.post('range', range)

        except AttributeError as e:
            print(e)

    def keyPressEvent(self, event):
        if event.key() == 16777220:
            self.update_editor()

    def openMenu(self, pos):
        item = self.itemAt(pos)
        globalPos = self.mapToGlobal(pos)

        if item.node == 'knob':
            knob = item.name
            device = item.parent().name
            hub = item.parent().parent().name
            params = {'knob': knob, 'device': device, 'hub': hub}
            options = self.dashboard.get('hubs/%s/devices/%s/knobs/%s/options'%(hub, device, knob))
        elif item.node == 'device':
            knob = None
            device = item.name
            hub = item.parent().name
            params = {'device': device, 'hub': hub}
            options = self.dashboard.get('hubs/%s/devices/%s/options'%(hub, device))
        elif item.node == 'hub':
            knob = None
            device = None
            hub = item.name
            params = {'hub': hub}
            options = self.dashboard.get('hubs/%s/options'%hub)

        if options == []:
            return
        actions = {}
        for option in options:
            actions[option] = partial(self.exec_option, params, option)
        menu = DictMenu(actions)

        selectedItem = menu.exec_(globalPos)

    def exec_option(self, params, option):
        ''' Takes a params dict containing a node specified by knob, device, hub
            and a key corresponding to the options dict on the node '''
        d = {}
        for key in params:
            d[key] = params[key]
        d['method'] = option

        url = 'hubs/%s'%params['hub']
        if 'device' in params:
            url += '/devices/%s'%params['device']
        if 'knob' in params:
            url += '/knobs/%s'%params['knob']
        url += '/exec'
        self.dashboard.post(url, {'method': 'exec_option', 'args': (option,)})

from emergent.utilities.signals import FloatSignal

class HubWidget(QTreeWidgetItem):
    def __init__(self, name):
        super().__init__([name])
        self.name = name
        self.node = 'hub'

class DeviceWidget(QTreeWidgetItem):
    def __init__(self, name):
        super().__init__([name])
        self.name = name
        self.node = 'device'

class KnobWidget(QTreeWidgetItem):
    def __init__(self, name):
        super().__init__([name])
        self.name = name
        self.node = 'knob'
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

    def move(self, n):
        ''' Moves the widget n steps up (negative n) or down (positive n)
            in the tree '''
        current_index = self.parent().indexOfChild(self)
        if current_index == 0 and n < 0:
            return
        if current_index == self.parent().childCount()-1 and n > 0:
            return
        parent = self.parent()
        parent.takeChild(current_index)
        parent.insertChild(current_index+n, self)
