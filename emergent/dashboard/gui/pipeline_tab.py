''' The OptimizeTab allows the user to choose algorithms and their parameters and
    launch optimizations. '''
from PyQt5.QtWidgets import (QComboBox, QPushButton, QTabWidget, QVBoxLayout, QWidget,
        QTableWidgetItem, QTableWidget, QHBoxLayout, QGridLayout, QLabel, QMenu, QAction,
        QTreeWidget, QTreeWidgetItem, QToolBar, QAbstractItemView, QHeaderView, QHBoxLayout)
from PyQt5.QtCore import *
from PyQt5.QtGui import QCursor
from emergent.modules.parallel import ProcessHandler
import logging as log
import numpy as np
from emergent.dashboard.gui.parameter_table import ParameterTable
from emergent.utilities import recommender
import importlib, inspect

class CustomTree(QTreeWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.itemDoubleClicked.connect(self.open_editor)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.header().setMinimumSectionSize(200)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

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
        self.parent = parent

        hlayout = QHBoxLayout()
        self.addLayout(hlayout)

        vlayout = QVBoxLayout()
        hlayout.addLayout(vlayout)
        self.experiment_box = QComboBox()

        vlayout.addWidget(self.experiment_box)
        self.experiment_box.currentTextChanged.connect(self.update_params)

        ''' Experiment parameters '''
        self.experiment_table = ParameterTable()
        vlayout.addWidget(self.experiment_table)



        self.tree = CustomTree(self)
        self.tree.setColumnCount(2)
        header_item = QTreeWidgetItem(['Block', 'Parameter'])
        self.tree.setHeaderItem(header_item)
        self.tree.setDragEnabled(True)
        self.tree.viewport().setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QAbstractItemView.InternalMove)

        hlayout.addWidget(self.tree)

        self.menu = QMenu()
        self.setMenuBar(self.menu)

        self.actions = {}
        import functools

        self.submenu = self.menu.addMenu('Add')

        self.opt_submenu = self.submenu.addMenu('Optimizers')
        for action in self.list_optimizers():
            self.actions[action] = self.opt_submenu.addAction(action)
            self.actions[action].triggered.connect(functools.partial(self.menu_option, action))
        # self.model_submenu = self.submenu.addMenu('Models')
        # for action in self.list_models():
        #     self.actions[action] = self.model_submenu.addAction(action)
        #     self.actions[action].triggered.connect(functools.partial(self.menu_option, action))
        self.block_submenu = self.submenu.addMenu('Blocks')
        for action in self.list_blocks():
            self.actions[action] = self.block_submenu.addAction(action)
            self.actions[action].triggered.connect(functools.partial(self.menu_option, action))

        self.button = QPushButton('Run')
        self.button.clicked.connect(self.post_pipeline)
        self.addWidget(self.button)


    def menu_option(self, action):
        self.add_block({'name': action})
        self.menu.exec()

    def openMenu(self, pos):
        item = self.itemAt(pos)
        globalPos = self.mapToGlobal(pos)
        menu = QMenu()
        options = ['GridSearch', 'ParticleSwarm', 'DifferentialEvolution']
        func = lambda name=n: self.add_block({'name': n})
        for option in options:
            actions[option] = QAction(option, self)
            actions[option].triggered.connect(func(option))
            menu.addAction(actions[option])
        selectedItem = menu.exec_(globalPos)

    def add_block(self, d, position=None):
        if position is None or self.tree.currentItem() is None:
            position = self.tree.topLevelItemCount()
        name = d['name']
        root = QTreeWidgetItem([name])
        root.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled)
        # root.setFlags(root.flags() & ~Qt.ItemIsSelectable)

        self.tree.insertTopLevelItems(position, [root])

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

    def update_params(self):
        experiment = self.experiment_box.currentText()
        if experiment == '':
            return
        hub = self.parent.dashboard.tree_widget.get_selected_hub()
        d = self.parent.dashboard.get('hubs/%s/experiments/%s'%(hub, experiment))
        self.experiment_table.set_parameters(d['experiment'])

    def post_pipeline(self):
        print('Posting new pipeline')
        payload = {}
        payload['state'] = self.parent.dashboard.tree_widget.get_selected_state()
        payload['blocks'] = self.get_pipeline()
        payload['range'] = self.parent.dashboard.tree_widget.get_selected_range()
        payload['experiment'] = self.experiment_box.currentText()
        payload['params'] = self.experiment_table.get_params()
        self.parent.dashboard.post('hubs/hub/pipeline/new', payload)

        self.tree.clear()
