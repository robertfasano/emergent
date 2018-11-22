from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QHBoxLayout, QCheckBox, QTabWidget, QLineEdit, QSlider, QGridLayout)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import random
from matplotlib.figure import Figure
import json
plt.ioff()

class PlotWidget(QWidget):
    def __init__(self, sampler, algorithm, inputs, hist_fig, cvp, pvt, fig2d, parent = None, title=''):
        super(PlotWidget, self).__init__(parent)
        self.sampler = sampler
        self.algorithm = algorithm
        self.canvas = []
        self.layout = QVBoxLayout(self)
        self.setWindowTitle(title)
        self.tabs = QTabWidget()
        self.inputs = inputs
        self.layout.addWidget(self.tabs)
        self.tabs.currentChanged.connect(self.draw)

        self.cvp = cvp
        self.pvt = pvt
        self.fig2d = fig2d
        self.hist_fig = hist_fig


        ''' info tab '''
        self.info_tab = QWidget()
        self.tabs.addTab(self.info_tab, "Summary")
        self.vert_layout = QVBoxLayout()
        self.layout = QGridLayout()
        self.info_tab.setLayout(self.vert_layout)
        self.vert_layout.addLayout(self.layout)
        self.layout.addWidget(QLabel('Experiment:'), 0, 1)
        self.layout.addWidget(QLabel(self.sampler.cost_name), 0, 2)

        self.layout.addWidget(QLabel('Inputs:'), 0, 0)
        inputs_string = json.dumps(self.sampler.inputs).replace('{', '').replace('}', '').replace('],', ']\n').replace('"', '')
        self.layout.addWidget(QLabel(inputs_string), 1,0)

        self.layout.addWidget(QLabel('Experiment parameters'), 1, 1)
        cost_params = self.sampler.cost_params
        cost_params = str(cost_params).replace('{', '').replace(',', ',\n').replace('}', '')

        self.layout.addWidget(QLabel(cost_params), 1, 2)
        self.layout.addWidget(QLabel('Algorithm'), 0, 3)
        self.layout.addWidget(QLabel(algorithm), 0, 4)

        self.layout.addWidget(QLabel('Algorithm parameters'), 1, 3)
        params = self.sampler.params
        params = str(params).replace('{', '').replace(',', ',\n').replace('}', '')
        self.layout.addWidget(QLabel(params), 1, 4)


        ''' optimization history '''

        self.canvas_hist = FigureCanvas(self.hist_fig)

        self.vert_layout.addWidget(self.canvas_hist)
        self.canvas_hist.draw()

        ''' 1D tab '''
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.addTab(self.tab1,"1D")
        # self.fig1 = fig1
        # self.canvas1 = FigureCanvas(self.fig1)
        self.tab1_layout = QVBoxLayout()

        self.tab1_input_layout = QHBoxLayout()
        self.input_box = QComboBox()
        self.tab1_input_layout.addWidget(self.input_box)
        for input in self.inputs:
            self.input_box.addItem(input)
        self.input_box.currentTextChanged.connect(self.choose_input)
        self.tab1_layout.addLayout(self.tab1_input_layout)

        self.tab1_plot_layout = QHBoxLayout()
        self.tab1_layout.addLayout(self.tab1_plot_layout)
        # self.tab1_layout.addWidget(self.canvas1)
        self.tab1.setLayout(self.tab1_layout)
        # self.canvas1.draw()

        self.canvas1 = None
        self.canvas2 = None
        self.canvas2d = None
        self.canvas = [self.canvas1]

        self.choose_input()

        ''' 2d tab '''
        if len(inputs) > 1:
            self.axis_combos = list(self.fig2d.keys())
            self.tab2d = QWidget()
            self.tabs.addTab(self.tab2d,"2D")
            self.tab2d_layout = QVBoxLayout()
            self.tab2d.setLayout(self.tab2d_layout)

            self.tab2d_inputs_layout = QHBoxLayout()
            self.axis_combo_box = QComboBox()
            self.tab2d_inputs_layout.addWidget(self.axis_combo_box)
            for pair in self.axis_combos:
                self.axis_combo_box.addItem(pair)
            self.axis_combo_box.currentTextChanged.connect(self.choose_input_pair)
            self.tab2d_layout.addLayout(self.tab2d_inputs_layout)
            self.choose_input_pair()




    def choose_input(self):
        if self.canvas1 is not None:
            self.tab1_plot_layout.removeWidget(self.canvas1)
            self.canvas1.deleteLater()
        if self.canvas2 is not None:
            self.tab1_plot_layout.removeWidget(self.canvas2)
            self.canvas2.deleteLater()
        input = self.input_box.currentText()
        self.canvas1 = FigureCanvas(self.cvp[input])
        self.canvas2 = FigureCanvas(self.pvt[input])

        self.tab1_plot_layout.addWidget(self.canvas1)
        self.tab1_plot_layout.addWidget(self.canvas2)

        self.canvas1.draw()
        self.canvas2.draw()

    def choose_input_pair(self):
        if self.canvas2d is not None:
            self.tab2d_layout.removeWidget(self.canvas2d)
            self.canvas2d.deleteLater()

        pair = self.axis_combo_box.currentText()
        self.canvas2d = FigureCanvas(self.fig2d[pair])

        self.tab2d_layout.addWidget(self.canvas2d)
        self.canvas2d.draw()

    def addTab(self, fig):
        self.tab2 = QWidget()
        self.tabs.addTab(self.tab2,"2D")
        self.fig2 = fig
        self.canvas2d = FigureCanvas(self.fig2)
        self.tab2_layout = QVBoxLayout()
        self.tab2_layout.addWidget(self.canvas2d)
        self.tab2.setLayout(self.tab2_layout)
        self.canvas2d.draw()
        self.canvas.append(self.canvas2d)
        # self.tabs.setCurrentIndex(1)

    def draw(self):
        for c in self.canvas:
            if c is not None:
                c.draw()
