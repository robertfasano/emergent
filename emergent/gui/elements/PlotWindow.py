from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QHBoxLayout, QCheckBox, QTabWidget, QLineEdit, QSlider)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import random
from matplotlib.figure import Figure
plt.ioff()

class PlotWidget(QWidget):
    def __init__(self, fig1, fig2 = None, parent = None, title=''):
        super(PlotWidget, self).__init__(parent)
        self.canvas = []
        self.layout = QVBoxLayout(self)
        self.setWindowTitle(title)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        self.tabs.currentChanged.connect(self.draw)

        #GUI configuration
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.addTab(self.tab1,"1D")
        self.fig1 = fig1
        self.canvas1 = FigureCanvas(self.fig1)
        layout1 = QVBoxLayout()
        layout1.addWidget(self.canvas1)
        self.tab1.setLayout(layout1)
        self.canvas1.draw()

        self.canvas = [self.canvas1]

    def addTab(self, fig):
        self.tab2 = QWidget()
        self.tabs.addTab(self.tab2,"2D")
        self.fig2 = fig
        self.canvas2 = FigureCanvas(self.fig2)
        layout2 = QVBoxLayout()
        layout2.addWidget(self.canvas2)
        self.tab2.setLayout(layout2)
        self.canvas2.draw()
        self.canvas.append(self.canvas2)
        self.tabs.setCurrentIndex(1)

    def draw(self):
        for c in self.canvas:
            c.draw()
