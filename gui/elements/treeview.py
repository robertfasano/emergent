#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import types
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QFont
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
        QGroupBox, QHBoxLayout, QLabel, QLineEdit, QTreeView, QTableView,QVBoxLayout,
        QWidget, QMenu, QAction)
from PyQt5.QtCore import *

class MainFrame(QWidget):
    def __init__(self, tree, control):
        QWidget.__init__(self)
        self.control = control
        self.tree = QTreeView(self)
        font = QFont("Agency FB")
        self.tree.setFont(font)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.openMenu)
        layout = QHBoxLayout(self)
        layout.addWidget(self.tree)

        root_model = QStandardItemModel()
        root_model.setHorizontalHeaderLabels(['Node', 'Value'])
        root_model.setColumnCount(2)

        self.tree.setModel(root_model)
        self._populateTree(tree, root_model.invisibleRootItem())

    def _populateTree(self, children, parent):
        for child in sorted(children):
            child_item = QStandardItem(child)
            parent.appendRow(child_item)
            parent.appendColumn([QStandardItem('')])
            if isinstance(children, dict):
                self._populateTree(children[child], child_item)

    def openMenu(self, pos):
        level = self.get_selected_level()
        globalPos = self.mapToGlobal(pos)
        menu = QMenu()
        echoAction = QAction('Value', self)
        echoAction.triggered.connect(self.get_selected_value)

        if level == 2:
            menu.addAction(echoAction)
        selectedItem = menu.exec_(globalPos)

    def get_selected_level(self):
        indexes = self.tree.selectedIndexes()
        level = 0
        index = indexes[0]
        while index.parent().isValid():
            index = index.parent()
            level += 1
        return level

    def get_selected_item(self):
        indexes = self.tree.selectedIndexes()
        return indexes[0].model().itemFromIndex(indexes[0])

    def get_selected_key(self):
        item = self.get_selected_item()
        input = item.text()
        device = item.parent().text()
        key = device + '.' + input

        return key

    def get_selected_value(self):
        value = self.control.state[self.get_selected_key()]
        item = self.get_selected_item()
        #self.tree.model().setItem(1,1,QStandardItem(str(value)))
        item.insertColumn(1,[QStandardItem(str(value))])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = MainFrame()
    main.show()
    sys.exit(app.exec_())
