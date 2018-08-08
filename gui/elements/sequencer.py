from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QTableWidget, QTableWidgetItem, QHBoxLayout)
from PyQt5.QtCore import *
from archetypes.optimizer import Optimizer
import inspect
import json

class SequencerLayout(QVBoxLayout):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        self.parent = parent

        self.addWidget(QLabel('Sequencer'))

        self.table = QTableWidget()
        self.addWidget(self.table)
        self.parent.treeLayout.treeWidget.itemSelectionChanged.connect(self.update_input)

        self.buttonsLayout = QHBoxLayout()
        self.start_button = QPushButton('Start')
        self.start_button.clicked.connect(self.start)
        self.buttonsLayout.addWidget(self.start_button)

        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop)
        self.buttonsLayout.addWidget(self.stop_button)

        self.addLayout(self.buttonsLayout)
    def start(self):
        tree = self.parent.treeLayout.treeWidget
        item = tree.currentItem()
        control = item.root
        control.clock.start()

    def stop(self):
        tree = self.parent.treeLayout.treeWidget
        item = tree.currentItem()
        control = item.root
        control.clock.stop()

    def update_input(self):
        ''' Updates the sequencer table to the currently selected input. '''
        tree = self.parent.treeLayout.treeWidget
        control = tree.currentItem().root
        control.clock.prepare_sequence()
        ''' Only show active inputs based on real/virtual selection in tree '''
        seq = control.master_sequence
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        item = QTableWidgetItem()
        item.setText('Time')
        self.table.setVerticalHeaderItem(0,item)
        first_loop = True

        for point in seq:
            col = self.table.columnCount()
            self.table.insertColumn(col)
            item = QTableWidgetItem()
            item.setText(str(point[0]))
            self.table.setHorizontalHeaderItem(col,item)
            row = 0
            for key in point[1].keys():
                input = self.parent.treeLayout.get_input(key)
                device = input.parent()
                input_type = input.node.type
                if input_type == device.inputs:
                    if first_loop:
                        self.table.insertRow(row)
                    item = QTableWidgetItem()
                    item.setText(key)
                    self.table.setVerticalHeaderItem(row,item)

                    item = QTableWidgetItem()
                    item.setText(str(point[1][key]))
                    self.table.setItem(row, col, item)
                    row += 1
            first_loop = False
