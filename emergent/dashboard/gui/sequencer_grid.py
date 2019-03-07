
from PyQt5.QtWidgets import (QApplication, QComboBox, QLabel, QVBoxLayout, QLineEdit, QLayout, QScrollArea,
        QWidget, QCheckBox, QHBoxLayout, QTabWidget, QGridLayout, QMenu, QAction, QTreeWidget, QTreeWidgetItem, QSizePolicy)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from emergent.gui.elements.ParameterTable import ParameterTable
from matplotlib.figure import Figure
plt.ioff()
from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QCursor, QPixmap, QPainter

class VerticalLabel(QWidget):
    def __init__(self, text=None):
        super(self.__class__, self).__init__()
        self.text = text

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.black)
        painter.translate(20, 100)
        painter.rotate(-90)
        if self.text:
            painter.drawText(0, 0, self.text)
        painter.end()

class StateCheckbox(QCheckBox):
    def __init__(self, timestep, channel):
        super().__init__()
        self.timestep = timestep
        self.channel = channel
        self.picklable = False
        self.setChecked(self.timestep['state'][self.channel])
        self.stateChanged.connect(self.onChanged)

    def onChanged(self, state):
        self.timestep['state'][self.channel] = int(self.isChecked())
        # if self.sequencer is not None:
        #     if self.timestep['name'] == self.sequencer.current_step:
        #         self.sequencer.goto(self.timestep['name'])

class StepEdit(QLineEdit):
    def __init__(self, name, text, dashboard, hub):
        super().__init__(text)
        self.picklable = False
        self.dashboard = dashboard
        self.hub = hub
        self.name = name
        self.returnPressed.connect(self.onReturn)
        self.setMaximumWidth(75)
        self.setFixedWidth(75)

    def onReturn(self):
        state = {self.hub: {'sequencer':{self.name: float(self.text())}}}
        self.dashboard.p2p.set('state', state)
        self.dashboard.actuate_signal.emit(state)

class BoldLabel(QLabel):
    def __init__(self, name):
        super().__init__(name)
        self.name = name

    def setBold(self, bold):
        if bold:
            self.setText('<b>'+self.name+'</b>')
        else:
            self.setText(self.name)

class GridWindow(QWidget):
    def __init__(self, dashboard, hub):
        super(GridWindow, self).__init__(None)
        with open('gui/stylesheet.txt', "r") as file:
            self.setStyleSheet(file.read())
        self.setWindowTitle('Timing grid')
        self.setObjectName('timingGrid')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding);
        self.dashboard = dashboard
        self.hub = hub
        self.picklable = False

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.widget = QWidget()
        self.grid_layout = QGridLayout()
        self.widget.setLayout(self.grid_layout)
        self.layout.addWidget(self.widget)

        self.switches = self.dashboard.p2p.get('switches', params={'hub': self.hub})
        ''' Create switch labels '''
        row = 2
        for switch in self.switches:
            self.grid_layout.addWidget(QLabel(switch), row, 0)
            row += 1

        self.draw()

        self.dashboard.actuate_signal.connect(self.actuate)

    def draw(self):
        self.labels = {}
        self.step_edits = {}
        self.checkboxes = {}
        timesteps = self.dashboard.p2p.get('timesteps', params={'hub': self.hub})
        col = 1
        for step in timesteps:
            self.add_step(step, col)
            col += 1
        # self.bold_active_step()

    def redraw(self):
        for step in self.labels:
            self.remove_step(step)
        self.draw()
        QApplication.processEvents()        # determine new minimumSize
        self.resize(self.minimumSize())

    def add_step(self, step, col):
        ''' Add label and edit '''
        self.labels[step['name']] = BoldLabel(step['name'])
        self.grid_layout.addWidget(self.labels[step['name']], 0, col)
        self.step_edits[step['name']] = StepEdit(step['name'], str(step['duration']), self.dashboard, self.hub)
        self.grid_layout.addWidget(self.step_edits[step['name']], 1, col)

        ''' Add checkboxes '''
        row = 2
        self.checkboxes[step['name']] = {}
        for switch in self.switches:
            box = StateCheckbox(step, switch)
            self.grid_layout.addWidget(box, row, col)
            self.checkboxes[step['name']][switch] = box
            row += 1

    # def remove_step(self, step):
    #     remove = [self.labels[step], self.step_edits[step]]
    #     for switch in self.sequencer.parent.switches:
    #         remove.append(self.checkboxes[step][switch])
    #     for widget in remove:
    #         self.grid_layout.removeWidget(widget)
    #         widget.deleteLater()

    #
    # def bold_active_step(self):
    #     for step in self.sequencer.steps:
    #         if step['name'] == self.sequencer.current_step:
    #             self.labels[step['name']].setBold(True)
    #         else:
    #             self.labels[step['name']].setBold(False)

    def actuate(self, state):
        try:
            state = state[self.hub]['sequencer']
        except KeyError:
            return
        for step_name in self.step_edits:
            if step_name in state:
                self.step_edits[step_name].setText(str(state[step_name]))
