
from PyQt5.QtWidgets import (QComboBox, QLabel, QVBoxLayout, QLineEdit, QLayout,
        QWidget, QCheckBox, QHBoxLayout, QTabWidget, QGridLayout, QMenu, QAction, QTreeWidget, QTreeWidgetItem)
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
    def __init__(self, timestep, channel, sequencer):
        super().__init__()
        self.timestep = timestep
        self.channel = channel
        self.sequencer = sequencer
        self.picklable = False
        self.setChecked(self.timestep.state[self.channel])
        self.stateChanged.connect(self.onChanged)

    def onChanged(self, state):
        self.timestep.state[self.channel] = int(self.isChecked())
        if self.sequencer is not None:
            if self.timestep.name == self.sequencer.current_step:
                self.sequencer.goto(self.timestep.name)


class SwitchWindow(QWidget):
    def __init__(self, timestep):
        super(SwitchWindow, self).__init__(None)
        layout = QGridLayout()
        self.setLayout(layout)
        self.picklable = False
        self.checkboxes = {}
        row = 0
        for ch in timestep.state:
            layout.addWidget(QLabel(ch), row, 0)
            self.checkboxes[ch] = StateCheckbox(timestep, ch, None)
            layout.addWidget(self.checkboxes[ch], row, 1)
            row += 1

class StepEdit(QLineEdit):
    def __init__(self, name, text, sequencer):
        super().__init__(text)
        self.picklable = False
        self.name = name
        self.sequencer = sequencer
        self.returnPressed.connect(self.onReturn)
        self.setMaximumWidth(75)
        self.setFixedWidth(75)
        
    def onReturn(self):
        self.sequencer.parent.actuate({'sequencer':{self.name: float(self.text())}})

class GridWindow(QWidget):
    def __init__(self, sequencer):
        super(GridWindow, self).__init__(None)
        with open('gui/stylesheet.txt', "r") as file:
            self.setStyleSheet(file.read())
        self.setWindowTitle('Timing grid')
        self.sequencer = sequencer
        self.picklable = False
        layout = QGridLayout()
        self.setLayout(layout)
        ''' Create switch labels '''
        row = 2
        for switch in self.sequencer.parent.switches:
            layout.addWidget(QLabel(switch), row, 0)
            row += 1

        ''' Create step labels '''
        col = 1
        for step in self.sequencer.steps:
            layout.addWidget(QLabel(step.name), 0, col)
            layout.addWidget(StepEdit(step.name, str(self.sequencer.state[step.name]), self.sequencer), 1, col)
            col += 1

        ''' Create checkboxes '''
        col = 1
        for step in self.sequencer.steps:
            row = 2
            for switch in self.sequencer.parent.switches:
                layout.addWidget(StateCheckbox(step, switch, self.sequencer), row, col)
                row += 1
            col += 1

    def update_duration(self):
        return
