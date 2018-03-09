import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pyqtgraph.Qt import QtCore as pgCore
import pyqtgraph as pg
import os
import sys
if os.name == 'posix':        # if using OS X, open a special testing version of the program
    sys.path.append('C:\\Users\\Public\\Documents\\GitHub')
else:
    sys.path.append('/Users/rjf2/Documents/GitHub')
    
import labAPI.IO
from PyQt5.QtWidgets import QComboBox, QPushButton
import functools

class CustomViewBox(pg.ViewBox):
    def __init__(self, *args, **kwds):
        pg.ViewBox.__init__(self, *args, **kwds)
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

class Clickable(QPushButton):
    def __init__(self, name, tab, function, args = None):
        super().__init__()
        self.setText(name)
        if args == None:
            self.clicked.connect(functools.partial(function))
        else:
            self.clicked.connect(functools.partial(function, args))
        self.setStyleSheet(tab.buttonStyle)                
            
class Plotter():
    def __init__(self, tab, row, col, height, width, filename, timecols = 2):
        self.tab = tab
        self.row = row
        self.col = col
        self.height = height
        self.width = width
        self.filename = filename
        self.tab.plotterWindow = pg.GraphicsWindow(title="Data visualizer")
        pg.setConfigOptions(antialias=True)
        self.tab.layout.addWidget(self.tab.plotterWindow,row, col, height, width)
        
        ''' Create combo box of plottable quantities '''
        with open(filename, 'r') as file:
            self.watchpoints = labAPI.IO.parseRow(file.readlines()[0])[timecols::]
        self.tab.plotterComboBox = QComboBox()
        for item in self.watchpoints:
            self.tab.plotterComboBox.addItem(item)
        self.tab.plotterComboBox.activated.connect(self.plotSelect)
        self.tab.layout.addWidget(self.tab.plotterComboBox,self.row+self.height,self.col)

        ''' Create refresh button '''
        self.tab.plotRefreshButton = Clickable('Refresh', tab, self.plotSelect)
        self.tab.layout.addWidget(self.tab.plotRefreshButton, self.row+self.height, self.col+1)
        

    def plotSelect(self):
        choice = self.tab.plotterComboBox.currentText()
        try:
            data = pd.read_csv(self.filename,delimiter='\t',index_col = 0)
        except:
            data=pd.DataFrame(index=[], columns=range(1, len(self.watchpoints))) 
            print('ERROR: Could not read data!')
        self.plotDraw(choice, data)
        self.tab.layout.addWidget(self.plotter,self.row, self.col, self.height, self.width)

        
    def plotDraw(self,choice, df):   
        ''' Linked to the dropdown menu for ADC input choice; plots the user choice on the display 
        
        Arguments: 
            choice (str): the user-chosen value of the dropdown menu
        '''  
        vb = CustomViewBox()
        self.plotter = pg.PlotWidget(viewBox=vb)
        try:
            self.plotter.plot(df.index,df[choice].values, clear=True, title=choice)
        except Exception:
            pass