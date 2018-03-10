import os
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QComboBox, QPushButton
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

if os.name == 'posix':        # if using OS X, open a special testing version of the program
    sys.path.append('/Users/rjf2/Documents/GitHub')
else:
    sys.path.append('C:\\Users\\Public\\Documents\\GitHub')
    sys.path.append('C:\\Users\\Robbie\\Documents\\GitHub')

from labAPI import gui, IO
import pandas as pd
import numpy as np

class AnalysisTab(gui.Tab):
    def __init__(self, panel, clock):
        super().__init__('Analysis', panel)
        timecols = 2
        
        ''' Create canvas and navigation toolbar '''
        self.figure = plt.figure()
        self.figure.subplots_adjust(bottom=0.15, top=1, left=0.05, right=.95)

        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas, 1, 0, 2, 2)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        
        ''' Create combo box of plottable quantities '''
        with open(self.panel.filepath, 'r') as file:
            self.watchpoints = IO.parseRow(file.readlines()[0])[timecols::]
        self.choicebox = self._addComboBox(self.watchpoints, 3, 0)
        self.choicebox.activated.connect(self.plot)
        
        self.plots = ['Histogram', 'Time series']
        self.plotbox = self._addComboBox(self.plots, 3, 1)
        self.plotbox.activated.connect(self.plot)
        

    def plot(self):
        self.layout.addWidget(self.toolbar, 0, 0, 1, 2)
        if self.plotbox.currentText() == 'Histogram':
            self.histogram()
        elif self.plotbox.currentText() == 'Time series':
            self.timeSeries()
            
    def histogram(self):
        choice = self.choicebox.currentText()
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        data = pd.read_csv(self.panel.filepath,delimiter='\t',index_col = 0)[choice]
        ''' filter outliers '''
        n = 3
        data = data[np.abs(data-data.mean()) < n*data.std()]
        ''' plot data '''
        ax = data.hist(ax=ax)
#        ax.set_xlabel('%s (V)'%choice)
#        ax.set_ylabel('Counts')
        
        self.canvas.draw()
        
    def timeSeries(self):
        choice = self.choicebox.currentText()
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        data = pd.read_csv(self.panel.filepath,delimiter='\t',index_col = 0)[choice]
        
        data.plot(ax=ax)
#        ax.set_xlabel('MJD')
#        ax.set_ylabel('%s (V)'%choice)
        
        self.canvas.draw()

        



    