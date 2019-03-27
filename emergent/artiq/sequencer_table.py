from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QLabel, QCheckBox, QHeaderView
from PyQt5.QtCore import Qt

class TTLCheckbox(QCheckBox):
    def __init__(self, name, timestep, state, dashboard, hub, grid):
        super().__init__()
        self.name = name
        self.timestep = timestep
        self.dashboard = dashboard
        self.grid = grid
        self.hub = hub
        self.picklable = False
        self.setChecked(state)
        self.stateChanged.connect(self.onChanged)


class BoldLabel(QLabel):
    def __init__(self, name):
        super().__init__(name)
        self.name = name

    def setBold(self, bold):
        if bold:
            self.setText('<b>'+self.name+'</b>')
        else:
            self.setText(self.name)

class SequencerTable(QTableWidget):
    def __init__(self):
        QTableWidget.__init__(self)
        self.insertColumn(0)
        # self.horizontalHeader().setStretchLastSection(True)
        # self.horizontalHeader().setMinimumSectionSize(75)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # self.horizontalHeader().setFixedWidth(75)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.setShowGrid(False)
        # self.verticalScrollBar().setStyleSheet( " background-color: rgba(255, 255, 255, 0%) ")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff);
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);

    def set_channels(self, ttls):
        self.setRowCount(0)
        self.insertRow(0)
        self.insertRow(0)
        label = BoldLabel('TTL')
        label.setBold(True)
        self.setCellWidget(1, 0, label)

        for ttl in ttls:
            row = self.rowCount()
            self.insertRow(row)
            item = QTableWidgetItem(str(ttl))
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
            self.setItem(row, 0, item)
            row += 1

        self.insertRow(row)
        label = BoldLabel('ADC')
        label.setBold(True)
        self.setCellWidget(row, 0, label)

    def add_timestep(self, ttls, step):
        col = self.columnCount()
        self.insertColumn(col)
        name_item = QTableWidgetItem(step['name'])
        name_item.setFlags(name_item.flags() ^ Qt.ItemIsEditable)
        self.setItem(0, col, name_item)
        self.setItem(1, col, QTableWidgetItem(str(step['duration'])))
        row = 2
        for ttl in ttls:
            self.setCellWidget(row, col, QCheckBox())
            row += 1

    #
    # def get_params(self):
    #     params = State()
    #     for row in range(self.rowCount()):
    #         name = self.item(row, 0).text()
    #         if self.cellWidget(row, 1) is not None:
    #             value = self.cellWidget(row, 1).currentText()
    #             params[name] = value
    #             continue
    #         else:
    #             value = self.item(row, 1).text()
    #         if value == '[]':
    #             params[name] = []
    #         elif value == 'None':
    #             params[name] = None
    #         else:
    #             params[name] = float(value)
    #     return params
    #
    # def set_parameters(self, params):
    #     self.setRowCount(0)
    #     for p in sorted(params):
    #         # desc = self.get_description(panel, algo.name, p)
    #         self.add_parameter(p, str(params[p]))
    #
    # def add_parameter(self, name, value, description = ''):
    #     row = self.rowCount()
    #     self.insertRow(row)
    #     name_item = QTableWidgetItem(name)
    #     if description != '':
    #         name_item.setToolTip(description)
    #     name_item.setFlags(name_item.flags() ^ Qt.ItemIsEditable)
    #
    #     self.setItem(row, 0, name_item)
    #     self.setItem(row, 1, QTableWidgetItem(str(value)))
    #     try:
    #         if type(value) is not list:
    #             value = json.loads(value.replace("'", '"'))
    #         if type(value) is list:
    #             box = QComboBox()
    #             for item in value:
    #                 box.addItem(str(item))
    #             self.setCellWidget(row, 1, box)
    #     except json.JSONDecodeError:
    #         pass
