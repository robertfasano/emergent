
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
    def __init__(self, name, timestep, channel, dashboard, hub, grid):
        super().__init__()
        self.name = name
        self.timestep = timestep
        self.channel = channel
        self.dashboard = dashboard
        self.grid = grid
        self.hub = hub
        self.picklable = False
        self.setChecked(self.timestep['state'][self.channel])
        self.stateChanged.connect(self.onChanged)

    def onChanged(self, state):
        sequence = self.grid.get_sequence()
        params = {'hub': self.hub}
        self.dashboard.post('hubs/%s/sequencer/sequence'%self.hub, sequence)
        current_step = self.dashboard.get('hubs/%s/sequencer/current_step'%self.hub)
        if current_step == self.name:
            self.dashboard.post('hubs/%s/sequencer/current_step'%self.hub, {'step': self.name})

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
        self.dashboard.post('state', state)
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

        self.switches = self.dashboard.get('hubs/%s/switches'%self.hub)
        ''' Create switch labels '''
        row = 2
        for switch in self.switches:
            self.grid_layout.addWidget(QLabel(switch), row, 0)
            row += 1

        timesteps = self.dashboard.get('hubs/%s/sequencer/sequence'%self.hub)
        self.draw(timesteps)

        self.dashboard.actuate_signal.connect(self.actuate)

    def draw(self, sequence):
        self.labels = {}
        self.step_edits = {}
        self.checkboxes = {}
        col = 1
        for step in sequence:
            self.add_step(step, sequence[step], col)
            col += 1
        self.bold_active_step()

    def redraw(self, sequence):
        for step in self.labels:
            self.remove_step(step)
        self.draw(sequence)
        QApplication.processEvents()        # determine new minimumSize
        self.resize(self.minimumSize())

    def get_sequence(self):
        sequence = {}
        for step in self.labels:
            sequence[step] = {}
            sequence[step]['duration'] = self.step_edits[step].text()
            sequence[step]['state'] = {}
            for switch in self.switches:
                sequence[step]['state'][switch] = self.checkboxes[step][switch].isChecked()

        return sequence

    def add_step(self, name, step, col):
        ''' Add label and edit '''
        self.labels[name] = BoldLabel(name)
        self.grid_layout.addWidget(self.labels[name], 0, col)
        self.step_edits[name] = StepEdit(name, str(step['duration']), self.dashboard, self.hub)
        self.grid_layout.addWidget(self.step_edits[name], 1, col)

        ''' Add checkboxes '''
        row = 2
        self.checkboxes[name] = {}
        for switch in self.switches:
            box = StateCheckbox(name, step, switch, self.dashboard, self.hub, self)
            self.grid_layout.addWidget(box, row, col)
            self.checkboxes[name][switch] = box
            row += 1

    def remove_step(self, step):
        remove = [self.labels[step], self.step_edits[step]]
        for switch in self.switches:
            remove.append(self.checkboxes[step][switch])
        for widget in remove:
            self.grid_layout.removeWidget(widget)
            widget.deleteLater()

    def bold_active_step(self):
        steps = self.dashboard.get('hubs/%s/sequencer/sequence'%self.hub)
        current_step = self.dashboard.get('hubs/%s/sequencer/current_step'%self.hub)
        for step in steps:
            if step == current_step:
                self.labels[step].setBold(True)
            else:
                self.labels[step].setBold(False)

    def actuate(self, state):
        try:
            state = state[self.hub]['sequencer']
        except KeyError:
            return
        for step_name in self.step_edits:
            if step_name in state:
                self.step_edits[step_name].setText(str(state[step_name]))
