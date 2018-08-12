from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QTableWidget, QTableWidgetItem, QHBoxLayout)
from PyQt5.QtCore import *
from archetypes.optimizer import Optimizer
import inspect
import json

class MyTableWidgetItem(QTableWidgetItem):
    def __init__(self, node, parent=None):
        super().__init__()
        self.parent = parent
        self.node = node


class MyTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent

    def keyPressEvent(self, event):
         key = event.key()

         if key == Qt.Key_Return or key == Qt.Key_Enter:
             self.parent.update_item()

class SequencerLayout(QVBoxLayout):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        self.parent = parent

        self.addWidget(QLabel('Sequencer'))

        self.table = MyTableWidget(self)
        self.addWidget(self.table)
        self.parent.treeWidget.itemSelectionChanged.connect(self.update_input)

        self.table.itemDoubleClicked.connect(self.open_editor)
        self.buttonsLayout = QHBoxLayout()
        self.start_button = QPushButton('Start')
        self.start_button.clicked.connect(self.start)
        self.buttonsLayout.addWidget(self.start_button)

        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop)
        self.buttonsLayout.addWidget(self.stop_button)

        self.addLayout(self.buttonsLayout)

    def open_editor(self):
        ''' Allow the currently-selected node to be edited. '''
        self.table.openPersistentEditor(self.table.currentItem())

    def start(self):
        tree = self.parent.treeWidget
        item = tree.currentItem()
        control = item.root
        control.sequencer.start()

    def stop(self):
        tree = self.parent.treeWidget
        item = tree.currentItem()
        control = item.root
        control.sequencer.stop()

    def update_input(self):
        ''' Updates the sequencer table to the currently selected input. '''
        tree = self.parent.treeWidget
        control = tree.currentItem().root
        control.sequencer.prepare_sequence()

        ''' Only show active inputs based on primary/secondary selection in tree '''
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
                input = self.parent.treeWidget.get_input(key)
                device = input.parent()
                input_type = input.node.type
                if input_type == device.inputs:
                    if first_loop:
                        self.table.insertRow(row)
                    item = QTableWidgetItem()
                    item.setText(key)
                    self.table.setVerticalHeaderItem(row,item)

                    item = MyTableWidgetItem(node=input.node, parent=self)
                    item.setText(str(point[1][key]))
                    self.table.setItem(row, col, item)
                    row += 1
            first_loop = False

    def update_item(self):
        ''' Update sequence when Enter is pressed. '''
        try:
            currentItem = self.table.currentItem()
            row = self.table.currentRow()
            col = self.table.currentColumn()
            control = currentItem.node.parent.parent
            self.table.closePersistentEditor(currentItem)

            control.master_sequence[col][1][currentItem.node.full_name] = float(currentItem.text())
            for full_name in control.state:
                seq = control.sequencer.master_to_subsequence(full_name)
                control.inputs[full_name].sequence = seq
                control.sequence[full_name] = seq
        except AttributeError:
            pass
