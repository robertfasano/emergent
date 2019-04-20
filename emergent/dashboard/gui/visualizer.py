''' The PlotWidget class displays a summary of Sampler results with useful plots
    including:

    * Evaluated cost vs. time
    * Cost vs. knobs
    * Knobs vs. time
    * Custom algorithm plots, such as a 2D interpolated grid for GridSearch or a fitted kernel model for GaussianProcessRegression
'''

from PyQt5.QtWidgets import (QComboBox, QLabel, QVBoxLayout,
        QWidget, QHBoxLayout, QTabWidget, QGridLayout, QMenu, QAction, QTreeWidget, QTreeWidgetItem)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from emergent.dashboard.structures.parameter_table import ParameterTable
from matplotlib.figure import Figure
plt.ioff()
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QCursor, QPixmap
import pandas as pd
import pickle

class Canvas(FigureCanvas):
    def __init__(self, fig, parent):
        FigureCanvas.__init__(self, fig)
        self.parent = parent

    def contextMenuEvent(self, event):
        self.menu = QMenu(self)
        self.action = QAction('Clip')
        self.refresh = QAction('Refresh')
        self.refresh.triggered.connect(self.parent.update_figs)
        self.action.triggered.connect(self.save_to_clipboard)
        self.menu.addAction(self.action)
        self.menu.addAction(self.refresh)
        self.menu.popup(QCursor.pos())


    # def save_to_clipboard(self):
    #     pixmap = self.grab()
    #     self.app.clipboard().setPixmap(pixmap)

class PlotWidget(QWidget):
    def __init__(self, hub, sampler_id, cvp, pvt, parent=None):
        # super(PlotWidget, self).__init__(parent)
        super().__init__()
        # with open('dashboard/gui/stylesheet.txt',"r") as file:
        #     self.setStyleSheet(file.read())
        self.setStyleSheet('color:"#000000"; font-weight: light; font-family: "Exo 2"; font-size: 14px; background-color: white')
        self.parent = parent
        self.dashboard = self.parent.parent.dashboard
        self.sampler_id = sampler_id
        self.canvas = []
        self.layout = QVBoxLayout(self)
        self.setWindowTitle('Visualizer')
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        self.tabs.currentChanged.connect(self.draw)

        self.cvp = cvp
        self.pvt = pvt

        history = self.dashboard.get('hubs/%s/samplers/%s/data'%(hub, sampler_id))['history']
        history = pd.read_json(history)
        params = self.dashboard.get('hubs/%s/samplers/%s/parameters'%(hub, sampler_id))
        self.hist_fig = self.parent.plot_optimization(history, params['experiment']['name'])

        if 'model' in params:
            model = self.dashboard.get('hubs/%s/samplers/%s/model'%(hub, sampler_id), format='pickle')
        if 'algorithm' in params:
            algorithm = self.dashboard.get('hubs/%s/samplers/%s/algorithm'%(hub, sampler_id), format='pickle')

        ''' info tab '''
        self.info_tab = QWidget()

        self.tabs.addTab(self.info_tab, "Summary")
        self.vert_layout = QVBoxLayout()
        self.layout = QGridLayout()
        self.info_tab.setLayout(self.vert_layout)
        self.vert_layout.addLayout(self.layout)
        self.layout.addWidget(QLabel(params['experiment']['name']), 0, 1)

        self.layout.addWidget(QLabel('Knobs:'), 0, 0)

        tree = QTreeWidget()
        hub = params['hub']
        top = QTreeWidgetItem([hub])
        tree.insertTopLevelItems(0, [top])
        for device in params['knobs']:
            device_item = QTreeWidgetItem([device])
            top.addChild(device_item)
            for knob in params['knobs']:
                device_item.addChild(QTreeWidgetItem([knob]))
        tree.header().hide()
        tree.expandAll()
        self.layout.addWidget(tree, 1,0)

        cost_params = ParameterTable()
        cost_params.set_parameters(params['experiment']['params'])
        self.layout.addWidget(cost_params, 1, 1)

        if 'algorithm' in params:
            name = params['algorithm']['name']
        else:
            name = 'Measure'
        self.layout.addWidget(QLabel(name), 0, 2)
        algorithm_params = ParameterTable()
        if 'algorithm' in params:
            algorithm_params.set_parameters(params['algorithm']['params'])
        self.layout.addWidget(algorithm_params, 1, 2)


        ''' optimization history '''
        self.canvas_hist_layout = QHBoxLayout()
        self.vert_layout.addLayout(self.canvas_hist_layout)
        self.canvas_hist = None

        self.draw_hist_fig()
        knobs = []
        if not (self.cvp is None and self.pvt is None):
            ''' 1D tab '''
            self.tab1 = QWidget()
            self.tabs.addTab(self.tab1,"1D")
            self.tab1_layout = QVBoxLayout()

            self.tab1_knob_layout = QHBoxLayout()
            self.knob_box = QComboBox()
            self.tab1_knob_layout.addWidget(self.knob_box)
            for knob in list(cvp.keys()):
                knobs.append(knob)
                self.knob_box.addItem(knob)
            self.knob_box.currentTextChanged.connect(self.choose_knob)
            self.tab1_layout.addLayout(self.tab1_knob_layout)

            self.tab1_plot_layout = QHBoxLayout()
            self.tab1_layout.addLayout(self.tab1_plot_layout)
            self.tab1.setLayout(self.tab1_layout)

            self.canvas1 = None
            self.canvas2 = None
            self.canvas2d = None
            self.canvas = [self.canvas1]

            self.choose_knob()

        if len(knobs) == 2 and 'algorithm' in params:
            self.tab_algo = QWidget()
            fig = algorithm.plot()
            if fig is not None:
                self.tabs.addTab(self.tab_algo, '2D')
                self.canvas_algorithm = Canvas(fig, self)
                self.tab_algo_layout = QVBoxLayout(self.tab_algo)
                self.tab_algo_layout.addWidget(self.canvas_algorithm)
                self.canvas_algorithm.draw()

        if len(knobs) == 2 and 'model' in params:
            self.tab_model = QWidget()
            fig = model.plot()
            if fig is not None:
                self.tabs.addTab(self.tab_model, 'Model')
                self.canvas_model = Canvas(fig, self)
                self.tab_model_layout = QVBoxLayout(self.tab_model)
                self.tab_model_layout.addWidget(self.canvas_model)
                self.canvas_model.draw()

        # ''' Setup auto-update '''
        # self.update_timer = QTimer(self)
        # self.update_timer.timeout.connect(self.update_figs)
        # self.update_timer.start(1000)

    def choose_knob(self):
        if self.canvas1 is not None:
            self.tab1_plot_layout.removeWidget(self.canvas1)
            self.canvas1.deleteLater()
        if self.canvas2 is not None:
            self.tab1_plot_layout.removeWidget(self.canvas2)
            self.canvas2.deleteLater()
        knob = self.knob_box.currentText()
        self.canvas1 = Canvas(self.cvp[knob], self)
        self.canvas2 = Canvas(self.pvt[knob], self)

        self.tab1_plot_layout.addWidget(self.canvas1)
        self.tab1_plot_layout.addWidget(self.canvas2)

        self.canvas1.draw()
        self.canvas2.draw()

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
        self.hist_fig, self.cvp, self.pvt = self.parent.generate_figures()
        self.choose_knob()
        self.draw_hist_fig()
        if self.sampler.active and self.isVisible():
            return
        try:
            self.update_timer.stop()
        except AttributeError:
            pass
