''' The ParameterTable class is a custom implementation of QTableWidget whose display
    can be updated by passing a dict to set_parameters, and whose parameters can be
    obtained in dict form with get_params. '''

from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QComboBox
from PyQt5.QtCore import Qt
from emergent.utilities.containers import State
import json

class ParameterTable(QTableWidget):
    def __init__(self):
        QTableWidget.__init__(self)
        self.insertColumn(0)
        self.insertColumn(1)
        self.setHorizontalHeaderLabels(['Parameter', 'Value'])
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setMinimumSectionSize(100)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setFixedHeight(25)
        self.verticalHeader().hide()

        # self.verticalScrollBar().setStyleSheet( " background-color: rgba(255, 255, 255, 0%) ")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff);
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);

    def get_params(self):
        params = State()
        for row in range(self.rowCount()):
            name = self.item(row, 0).text()
            if self.cellWidget(row, 1) is not None:
                value = self.cellWidget(row, 1).currentText()
            else:
                value = self.item(row, 1).text()
            if value == '[]':
                params[name] = []
            elif value == 'None':
                params[name] = None
            else:
                params[name] = float(value)
        return params

    def set_parameters(self, params):
        self.setRowCount(0)
        for p in sorted(params):
            # desc = self.get_description(panel, algo.name, p)
            self.add_parameter(p, str(params[p]))

    def add_parameter(self, name, value, description = ''):
        row = self.rowCount()
        self.insertRow(row)
        name_item = QTableWidgetItem(name)
        if description != '':
            name_item.setToolTip(description)
        name_item.setFlags(name_item.flags() ^ Qt.ItemIsEditable)

        self.setItem(row, 0, name_item)
        self.setItem(row, 1, QTableWidgetItem(str(value)))
        try:
            value = json.loads(value)
            if type(value) == list:
                box = QComboBox()
                for item in value:
                    box.addItem(str(item))
                self.setCellWidget(row, 1, box)
        except json.JSONDecodeError:
            pass
