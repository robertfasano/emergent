from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QHBoxLayout, QTabWidget, QGridLayout, QMenu, QAction, QTreeWidget, QTreeWidgetItem)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import random
from emergent.gui.elements.ParameterTable import ParameterTable
from matplotlib.figure import Figure
import json
plt.ioff()
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QCursor, QPixmap

class Canvas(FigureCanvas):
    def __init__(self, fig, parent):
        FigureCanvas.__init__(self, fig)
        self.parent = parent
        self.app = self.parent.container.parent.parent.app

    def contextMenuEvent(self, event):
        self.menu = QMenu(self)
        self.action = QAction('Clip')
        self.refresh = QAction('Refresh')
        self.refresh.triggered.connect(self.parent.update_figs)
        self.action.triggered.connect(self.save_to_clipboard)
        self.menu.addAction(self.action)
        self.menu.addAction(self.refresh)
        self.menu.popup(QCursor.pos())


    def save_to_clipboard(self):
        pixmap = self.grab()
        self.app.clipboard().setPixmap(pixmap)

class PlotWidget(QWidget):
    def __init__(self, container, sampler, algorithm, inputs, hist_fig, cvp, pvt, fig2d, parent = None, title=''):
        super(PlotWidget, self).__init__(parent)
        with open('gui/stylesheet.txt',"r") as file:
            self.setStyleSheet(file.read())
        self.container = container
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
        self.layout.addWidget(QLabel(self.sampler.cost_name), 0, 2)

        self.layout.addWidget(QLabel('Inputs:'), 0, 0)

        tree = QTreeWidget()
        control = self.sampler.parent
        top = QTreeWidgetItem([control.name])
        tree.insertTopLevelItems(0, [top])
        for dev in self.sampler.inputs:
            dev_item = QTreeWidgetItem([dev])
            top.addChild(dev_item)
            for input in self.sampler.inputs[dev]:
                dev_item.addChild(QTreeWidgetItem([input]))
        tree.header().hide()
        tree.expandAll()
        self.layout.addWidget(tree, 1,0)



        cost_params = ParameterTable()
        cost_params.set_parameters(self.sampler.cost_params)
        self.layout.addWidget(cost_params, 1, 2)


        self.layout.addWidget(QLabel(algorithm), 0, 4)

        params = ParameterTable()
        params.set_parameters(self.sampler.params)
        self.layout.addWidget(params, 1, 4)


        ''' optimization history '''
        self.canvas_hist_layout = QHBoxLayout()
        self.vert_layout.addLayout(self.canvas_hist_layout)
        self.canvas_hist = None

        self.draw_hist_fig()


        ''' 1D tab '''
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.addTab(self.tab1,"1D")
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
        self.tab1.setLayout(self.tab1_layout)

        self.canvas1 = None
        self.canvas2 = None
        self.canvas2d = None
        self.canvas = [self.canvas1]

        self.choose_input()

        ''' 2d tab '''
        # if len(inputs) > 1 and self.container.process_type == 'optimize':
        #     self.axis_combos = list(self.fig2d.keys())
        #     self.tab2d = QWidget()
        #     self.tabs.addTab(self.tab2d,"2D")
        #     self.tab2d_layout = QVBoxLayout()
        #     self.tab2d.setLayout(self.tab2d_layout)
        #
        #     self.tab2d_inputs_layout = QHBoxLayout()
        #     self.axis_combo_box = QComboBox()
        #     self.tab2d_inputs_layout.addWidget(self.axis_combo_box)
        #     for pair in self.axis_combos:
        #         self.axis_combo_box.addItem(pair)
        #     self.axis_combo_box.currentTextChanged.connect(self.choose_input_pair)
        #     self.tab2d_layout.addLayout(self.tab2d_inputs_layout)
        #     self.choose_input_pair()

        if len(inputs) == 2:
            self.tab_algo = QWidget()
            self.tabs.addTab(self.tab_algo, 'Algorithm')
            fig = self.sampler.algorithm.plot()
            self.canvas_algorithm = Canvas(fig, self)
            self.tab_algo_layout = QVBoxLayout(self.tab_algo)
            self.tab_algo_layout.addWidget(self.canvas_algorithm)
            self.canvas_algorithm.draw()


        # ''' Setup auto-update '''
        # self.update_timer = QTimer(self)
        # self.update_timer.timeout.connect(self.update_figs)
        # self.update_timer.start(1000)

    def choose_input(self):
        if self.canvas1 is not None:
            self.tab1_plot_layout.removeWidget(self.canvas1)
            self.canvas1.deleteLater()
        if self.canvas2 is not None:
            self.tab1_plot_layout.removeWidget(self.canvas2)
            self.canvas2.deleteLater()
        input = self.input_box.currentText()
        self.canvas1 = Canvas(self.cvp[input], self)
        self.canvas2 = Canvas(self.pvt[input], self)

        self.tab1_plot_layout.addWidget(self.canvas1)
        self.tab1_plot_layout.addWidget(self.canvas2)

        self.canvas1.draw()
        self.canvas2.draw()


    def choose_input_pair(self):
        if self.canvas2d is not None:
            self.tab2d_layout.removeWidget(self.canvas2d)
            self.canvas2d.deleteLater()

        pair = self.axis_combo_box.currentText()
        self.canvas2d = Canvas(self.fig2d[pair], self)

        self.tab2d_layout.addWidget(self.canvas2d)
        self.canvas2d.draw()

    def draw(self):
        for c in self.canvas:
            if c is not None:
                c.draw()

    def draw_hist_fig(self):
        if self.canvas_hist is not None:
            self.canvas_hist_layout.removeWidget(self.canvas_hist)
            self.canvas_hist.deleteLater()
        self.canvas_hist = Canvas(self.hist_fig, self)
        self.canvas_hist_layout.addWidget(self.canvas_hist)
        self.canvas_hist.draw()

    def update_figs(self):
        self.hist_fig, self.cvp, self.pvt, self.fig2d = self.container.generate_figures()
        self.choose_input()
        self.draw_hist_fig()

        if not self.sampler.active:
            try:
                self.update_timer.stop()
            except AttributeError:
                pass
