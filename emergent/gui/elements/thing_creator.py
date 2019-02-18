
from PyQt5.QtWidgets import (QApplication, QComboBox, QLabel, QVBoxLayout, QLineEdit, QLayout, QScrollArea,
        QWidget, QCheckBox, QHBoxLayout, QTabWidget, QPushButton, QGridLayout, QMenu, QAction, QTreeWidget, QTreeWidgetItem, QSizePolicy)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from emergent.gui.elements.ParameterTable import ParameterTable
from matplotlib.figure import Figure
plt.ioff()
from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QCursor, QPixmap, QPainter
import inspect
import logging as log
import importlib

class ThingCreator(QWidget):
    def __init__(self, network):
        super(ThingCreator, self).__init__(None)
        self.network = network
        with open('gui/stylesheet.txt', "r") as file:
            self.setStyleSheet(file.read())
        self.setWindowTitle('New Thing')
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        ''' Hub selector '''
        self.hub_selector = QComboBox()
        self.layout.addWidget(self.hub_selector)
        for hub in network.hubs:
            self.hub_selector.addItem(hub)

        ''' Thing selector '''
        things = {}
        params = {}
        paths = ['emergent.things', 'emergent.networks.'+network.name+'.things']
        for path in paths:
            module = importlib.import_module(path)
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj):
                    try:
                        p = inspect.signature(obj).parameters['params'].default
                        params[obj.__name__] = p
                    except KeyError:
                        log.debug('Could not import %s: arguments not specified correctly.'%obj.__name__)
                        continue
                    things[obj.__name__] = obj

        self.things = things
        self.params = params
        self.thing_selector = QComboBox()
        self.layout.addWidget(self.thing_selector)
        for thing in self.things:
            self.thing_selector.addItem(thing)

        self.parameter_table = ParameterTable()
        self.layout.addWidget(self.parameter_table)
        self.thing_selector.currentTextChanged.connect(self.update_parameter_table)


        self.add_button = QPushButton('Add')
        self.add_button.clicked.connect(self.add_thing)
        self.layout.addWidget(self.add_button)


        self.update_parameter_table()

    def update_parameter_table(self):
        self.parameter_table.set_parameters(self.params[self.thing_selector.currentText()])

    def add_thing(self):
        thing = self.things[self.thing_selector.currentText()]
        params = self.parameter_table.get_params()
        hub = self.network.hubs[self.hub_selector.currentText()]
        new_thing = thing('test', params = params, parent = hub)
        hub.leaf.treeWidget().add_thing(hub, new_thing)
