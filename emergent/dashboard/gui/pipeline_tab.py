''' The OptimizeTab allows the user to choose algorithms and their parameters and
    launch optimizations. '''
from PyQt5.QtWidgets import (QComboBox, QPushButton, QTabWidget, QVBoxLayout, QWidget,
        QTableWidgetItem, QTableWidget, QMenu, QHBoxLayout, QGridLayout, QLabel,
        QTreeWidget, QInputDialog, QTreeWidgetItem, QToolBar, QAbstractItemView, QHeaderView, QHBoxLayout)
from PyQt5.QtCore import *
from PyQt5.QtGui import QCursor
import logging as log
import numpy as np
from emergent.dashboard.structures.parameter_table import ParameterTable
from emergent.dashboard.structures.dict_menu import DictMenu
from emergent.dashboard.structures.icon_button import IconButton
from emergent.utilities import recommender
import importlib, inspect
from functools import partial

class CustomTree(QTreeWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.itemDoubleClicked.connect(self.open_editor)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.header().setMinimumSectionSize(200)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.customContextMenuRequested.connect(self.openMenu)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

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

    def openMenu(self, pos):
        item = self.itemAt(pos)
        globalPos = self.mapToGlobal(pos)
        actions = {'Reset': self.parent.reset,
                   'Delete': lambda: self.delete_item(item)}
        actions['Add'] = {'Optimizer': {}, 'Model': {}, 'Block': {}}

        for block_type in ['optimizers', 'models', 'blocks']:
            blocks = self.parent.list_classes(block_type)
            subdict = actions['Add'][block_type.capitalize()[:-1]]
            for block in blocks:
                if item is not None:
                    if self.parent.is_pipeline(item.text(0)):
                        subdict[block] = partial(self.parent.add_block, {'name': block}, parent=item)
                    else:
                        subdict[block] = partial(self.parent.add_block, {'name': block})

                else:
                    subdict[block] = partial(self.parent.add_block, {'name': block})

        menu = DictMenu(actions)
        selectedItem = menu.exec_(globalPos)

    def delete_item(self, item):
        index = self.indexOfTopLevelItem(item)
        self.takeTopLevelItem(index)

class ModelOptimizerBox(QComboBox):
    def __init__(self, layout, tree_item, items):
        QComboBox.__init__(self)
        self.layout = layout
        self.tree_item = tree_item
        self.currentTextChanged.connect(self.update_subparams)

        for item in items:
            self.addItem(item)

    def update_subparams(self):
        for i in reversed(range(self.tree_item.childCount())):
            self.tree_item.removeChild(self.tree_item.child(i))

        subparams = self.layout.get_default_params(self.currentText())
        for s in subparams:
            subitem = QTreeWidgetItem([s])
            subitem.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled)
            subitem.setText(1, str(subparams[s]))
            self.tree_item.addChild(subitem)

class PipelineLayout(QVBoxLayout):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        self.parent = parent

        hlayout = QHBoxLayout()
        self.addLayout(hlayout)

        vlayout = QVBoxLayout()
        hlayout.addLayout(vlayout)
        box_layout = QHBoxLayout()
        vlayout.addLayout(box_layout)
        self.experiment_box = QComboBox()

        box_layout.addWidget(self.experiment_box)
        self.experiment_box.currentTextChanged.connect(self.update_params)
        box_layout.addWidget(IconButton('dashboard/gui/media/Material/content-save-outline.svg', self.save_params, tooltip='Save parameters'))
        box_layout.addWidget(IconButton('dashboard/gui/media/Material/content-undo.svg', self.reset_params, tooltip='Reset parameters'))


        ''' Experiment parameters '''
        self.experiment_table = ParameterTable()
        vlayout.addWidget(self.experiment_table)


        treeLayout = QVBoxLayout()
        hlayout.addLayout(treeLayout)

        saveLayout = QHBoxLayout()
        treeLayout.addLayout(saveLayout)
        self.pipeline_selector = QComboBox()
        self.pipeline_selector.addItem('default')
        saved=self.parent.dashboard.get('optimize/pipelines')
        for item in saved:
            self.pipeline_selector.addItem(item)
        self.pipeline_selector.currentTextChanged.connect(self.load)
        saveLayout.addWidget(self.pipeline_selector)
        self.store_button = IconButton('dashboard/gui/media/Material/content-save-outline.svg', self.store, tooltip='Save preset')
        saveLayout.addWidget(self.store_button)
        self.delete_button = IconButton('dashboard/gui/media/Material/trash.svg', self.delete, tooltip='Delete preset')
        saveLayout.addWidget(self.delete_button)

        self.tree = CustomTree(self)
        self.tree.setColumnCount(2)
        header_item = QTreeWidgetItem(['Block', 'Parameter'])
        self.tree.setHeaderItem(header_item)
        self.tree.setDragEnabled(True)
        self.tree.viewport().setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QAbstractItemView.InternalMove)

        treeLayout.addWidget(self.tree)

        self.add_button = IconButton('dashboard/gui/media/Material/content-add.svg', None, tooltip='Add block')
        self.add_button.setMenu(self.get_add_menu())
        self.remove_button = IconButton('dashboard/gui/media/Material/content-remove.svg', self.delete_item, tooltip='Remove block')
        self.clear_button = IconButton('dashboard/gui/media/Material/content-undo.svg', self.reset, tooltip='Reset pipeline')

        for button in [self.add_button, self.remove_button, self.clear_button]:
            saveLayout.addWidget(button)

        self.button = QPushButton('Run')
        self.button.clicked.connect(self.post_pipeline)
        self.addWidget(self.button)

        self.reset()

    def reset_params(self):
        experiment = self.experiment_box.currentText()
        if experiment == '':
            return
        hub = self.parent.dashboard.tree_widget.get_selected_hub()
        d = self.parent.dashboard.get('hubs/%s/experiments/%s/default'%(hub, experiment))
        self.experiment_table.set_parameters(d['experiment'])

    def save_params(self):
        experiment = self.experiment_box.currentText()
        if experiment == '':
            return
        hub = self.parent.dashboard.tree_widget.get_selected_hub()
        params = self.experiment_table.get_params()
        self.parent.dashboard.post('hubs/%s/experiments/%s'%(hub, experiment), {'params': params})

    def delete_item(self):
        items = self.tree.selectedItems()
        if items == []:
            return
        self.tree.delete_item(items[0])

    def get_add_menu(self):
        actions = {'Optimizer': {}, 'Model': {}, 'Block': {}}
        items = self.tree.selectedItems()
        for block_type in ['optimizers', 'models', 'blocks']:
            blocks = self.list_classes(block_type)
            subdict = actions[block_type.capitalize()[:-1]]
            for block in blocks:
                if items != []:
                    if self.is_pipeline(items[0].text(0)):
                        subdict[block] = partial(self.add_block, {'name': block}, parent=items[0])
                    else:
                        subdict[block] = partial(self.add_block, {'name': block})

                else:
                    subdict[block] = partial(self.add_block, {'name': block})

        return DictMenu(actions)

    def reset(self):
        self.tree.clear()
        self.add_block({'name': 'GridSearch'})

    def get_pipeline_blocks(self, item):
        name = item.text(0)
        d = {'name': name}
        d['params'] = {}
        for i in range(item.childCount()):
            c = item.child(i)
            child_name = c.text(0)

            if child_name == 'Blocks':
                d['subblocks'] = []
                for j in range(c.childCount()):
                    subchild = c.child(j)
                    d['subblocks'].append(self.get_pipeline_blocks(subchild))
            else:
                d['params'][child_name] = c.text(1)

        return d

    def to_json(self):
        blocks = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            blocks.append(self.get_pipeline_blocks(item))

        return blocks

    def from_json(self, blocks, parent=None):
        self.tree.clear()
        for block in blocks:
            item = self.add_block(block, parent=parent)
            if 'subblocks' in blocks:
                self.from_json(blocks['subblocks'], parent=item)

    def add_block(self, d, position=None, parent=None):
        ''' Args:
                d (dict): block description
                position (int): where to add the block
                parent (QTreeWidgetItem): parent of new block. If None, add top level item.
        '''
        if position is None and self.tree.currentItem() is None:
            position = self.tree.topLevelItemCount()
        else:
            position = self.tree.indexOfTopLevelItem(self.tree.currentItem())+1
        name = d['name']
        root = QTreeWidgetItem([name])
        root.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled)
        # root.setFlags(root.flags() & ~Qt.ItemIsSelectable)

        if parent is None:
            self.tree.insertTopLevelItems(position, [root])
        else:
            if self.is_pipeline(parent.text(0)):
                if not hasattr(parent, 'blocks'):
                    parent.blocks = QTreeWidgetItem(['Blocks'])
                    parent.addChild(parent.blocks)
                parent.blocks.addChild(root)

        params = self.get_default_params(name)
        if 'params' in d:
            for p in d['params']:
                params[p] = d['params'][p]
        for p in params:
            item = QTreeWidgetItem([p])
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled)
            if not isinstance(params[p], list):
                item.setText(1, str(params[p]))

            root.addChild(item)

            if isinstance(params[p], list):
                box = ModelOptimizerBox(self, item, self.list_classes('optimizers'))
                self.tree.setItemWidget(item, 1, box)
        return root


    def list_classes(self, module):
        ''' Returns a list of all classes in the targeted module.
            Args:
                module (str): one of ['optimizers', 'models', 'blocks']
        '''
        module = importlib.import_module('emergent.pipeline.%s'%module)
        names = []
        for a in dir(module):
            if '__' not in a:
                inst = getattr(module, a)
                if inspect.isclass(inst):
                    names.append(inst.__name__)
        return names

    def is_pipeline(self, name):
        module = getattr(importlib.import_module('emergent.pipeline'), name)
        has_blocks = hasattr(module(), 'blocks')
        return has_blocks

    def get_default_params(self, name):
        module = getattr(importlib.import_module('emergent.pipeline'), name)
        params = module().params

        params_dict = {}
        for p in params:
            params_dict[p] = params[p].value

        return params_dict

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
        payload['blocks'] = self.to_json()
        payload['range'] = self.parent.dashboard.tree_widget.get_selected_range()
        payload['experiment'] = self.experiment_box.currentText()
        payload['params'] = self.experiment_table.get_params()
        payload['hub'] = self.parent.dashboard.tree_widget.get_selected_hub()
        self.parent.dashboard.post('optimize/run', payload)

    def delete(self):
        name = self.pipeline_selector.currentText()
        if name == 'default':
            return
        # self.parent.dashboard.post('artiq/delete', {'name': name})
        self.pipeline_selector.removeItem(self.pipeline_selector.currentIndex())

    def store(self):
        name, ok = QInputDialog.getText(self.parent.dashboard, 'New pipeline', 'Enter preset name:')
        if not ok:
            return
        self.parent.dashboard.post('optimize/save', {'name': name, 'pipeline': self.to_json()})
        self.pipeline_selector.addItem(name)
        self.pipeline_selector.setCurrentIndex(self.pipeline_selector.count()-1)

    def load(self, name):
        if name == 'default':
            self.reset()
        else:
            pipe = self.parent.dashboard.get('optimize/pipelines/%s'%name)
            self.from_json(pipe)
