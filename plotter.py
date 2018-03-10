import pandas as pd
from pyqtgraph.Qt import QtCore as pgCore
import pyqtgraph as pg
import os
import sys
if os.name == 'posix':        # if using OS X, open a special testing version of the program
    sys.path.append('/Users/rjf2/Documents/GitHub')
else:
    sys.path.append('C:\\Users\\Public\\Documents\\GitHub')
    sys.path.append('C:\\Users\\Robbie\\Documents\\GitHub')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QComboBox, QPushButton
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import labAPI.IO
import functools
import matplotlib.pyplot as plt
import numpy as np

class CustomViewBox(pg.ViewBox):
    def __init__(self, plotter):
        self.plotter = plotter
        pg.ViewBox.__init__(self)
        self.setMouseMode(self.RectMode)
        
    ## reimplement right-click to zoom out
    def mouseClickEvent(self, ev):
        if ev.button() == pgCore.Qt.RightButton:
            self.autoRange()
            
    def mouseDragEvent(self, ev):
        if ev.button() == pgCore.Qt.RightButton:
            ev.ignore()
        else:
            pg.ViewBox.mouseDragEvent(self, ev)
            self.plotter.viewbox = self.getState()
            

class Clickable(QPushButton):
    def __init__(self, name, tab, function, args = None):
        super().__init__()
        self.setText(name)
        if args == None:
            self.clicked.connect(functools.partial(function))
        else:
            self.clicked.connect(functools.partial(function, args))
        self.setStyleSheet(tab.panel.styleButton)                
            
class Plotter():
    def __init__(self, tab, row, col, height, width, filename, timecols = 2):
        self.tab = tab
        self.row = row
        self.col = col
        self.height = height
        self.width = width
        self.filename = filename
        self.tab.plotterWindow = pg.GraphicsWindow(title="Data visualizer")
        self.tab.plotterWindow.resize(700,100)
        pg.setConfigOptions(antialias=True)
        self.tab.layout.addWidget(self.tab.plotterWindow,row, col, height, width)
        self.viewbox = 0
        
        ''' Create combo box of plottable quantities '''
        with open(filename, 'r') as file:
            self.watchpoints = labAPI.IO.parseRow(file.readlines()[0])[timecols::]
        self.tab.plotterComboBox = QComboBox()
        for item in self.watchpoints:
            self.tab.plotterComboBox.addItem(item)
        self.tab.plotterComboBox.activated.connect(self.plotSelect)
        self.tab.layout.addWidget(self.tab.plotterComboBox,self.row+self.height,self.col)

        ''' Create refresh button '''
        self.tab.plotRefreshButton = Clickable('Refresh', tab, self.plotSelect, args = 'refresh')
        self.tab.layout.addWidget(self.tab.plotRefreshButton, self.row+self.height, self.col+1)
        
        ''' Create uptime log '''
        self.tab.uptimeLog = self.tab._addLabel('', self.row+self.height+1, self.col)
        self.tab.uptimeTotal = self.tab._addLabel('', self.row+self.height+1, self.col+1)

    def uptime(self, choice):
        boolfile = self.filename.replace('log', 'bool')
        try:
            data = pd.read_csv(boolfile,delimiter='\t',index_col = 0)
        except:
            data=pd.DataFrame(index=[], columns=range(1, len(self.watchpoints))) 
            print('ERROR: Could not read data!')
        
        uptime = len(data[data[choice]==1])/len(data)
        self.tab.uptimeLog.setText('Uptime: %.0f%%'%(uptime*100))
        
        total = len(data[data['Human']==1])/len(data) * (data.iloc[-1]['Timestamp'] - data.iloc[0]['Timestamp'])
        self.tab.uptimeTotal.setText('Lock time today: %.0f minutes'%(total/60))

    def plotSelect(self, args = None):
        choice = self.tab.plotterComboBox.currentText()
        try:
            data = pd.read_csv(self.filename,delimiter='\t',index_col = 0)
        except:
            data=pd.DataFrame(index=[], columns=range(1, len(self.watchpoints))) 
            print('ERROR: Could not read data!')
        vb = CustomViewBox(self)
        self.plotter = pg.PlotWidget(viewBox=vb)
        
        try:
            self.plotter.plot(data.index,data[choice].values, clear=True, title=choice)
        except Exception:
            pass
        
        self.tab.layout.addWidget(self.plotter,self.row, self.col, self.height, self.width)
        self.uptime(choice)
        
        if args == 'refresh':
            if self.viewbox != 0:
                vb.setState(self.viewbox)

#class Plotter():
#    def __init__(self, tab, row, col, height, width, filename, timecols = 2):
#        timecols = 2
#        self.tab = tab
#        self.row = row
#        self.col = col
#        self.height = height
#        self.width = width
#        
#        ''' Create canvas and navigation toolbar '''
#        self.figure = plt.figure()
#        self.canvas = FigureCanvas(self.figure)
#        self.tab.layout.addWidget(self.canvas, self.row+1, self.col, self.height-1, self.width)
#        self.toolbar = NavigationToolbar(self.canvas, self.tab)
#        
#        
#        ''' Create combo box of plottable quantities '''
#        with open(self.tab.panel.filepath, 'r') as file:
#            self.watchpoints = labAPI.IO.parseRow(file.readlines()[0])[timecols::]
#        self.choicebox = self.tab._addComboBox(self.watchpoints, self.row+self.height+1, self.col)
#        self.choicebox.activated.connect(self.plot)
#        
#        self.plots = ['Histogram', 'Time series']
#        self.plotbox = self.tab._addComboBox(self.plots, self.row+self.height+1, self.col+1)
#        self.plotbox.activated.connect(self.plot)
#        
#
#    def plot(self):
#        self.tab.layout.addWidget(self.toolbar, self.row, self.col, 1, self.width)
#        if self.plotbox.currentText() == 'Histogram':
#            self.histogram()
#        elif self.plotbox.currentText() == 'Time series':
#            self.timeSeries()
#            
#    def histogram(self):
#        choice = self.choicebox.currentText()
#        self.figure.clear()
#        ax = self.figure.add_subplot(111)
#        plt.gcf().subplots_adjust(bottom=0.15)
#        data = pd.read_csv(self.tab.panel.filepath,delimiter='\t',index_col = 0)[choice]
#        ''' filter outliers '''
#        n = 3
#        data = data[np.abs(data-data.mean()) < n*data.std()]
#        ''' plot data '''
#        data.hist(ax=ax, figure=self.figure)
#        ax.set_xlabel('%s (V)'%choice)
#        ax.set_ylabel('Counts')
#        
#        self.canvas.draw()
#        
#    def timeSeries(self):
#        choice = self.choicebox.currentText()
#        self.figure.clear()
#        ax = self.figure.add_subplot(111)
#
#        data = pd.read_csv(self.tab.panel.filepath,delimiter='\t',index_col = 0)[choice]
#        
#        data.plot(ax=ax, figure = self.figure)
#        ax.set_xlabel('MJD')
#        ax.set_ylabel('%s (V)'%choice)
#        
#        self.canvas.draw() 
        
