import os
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QComboBox, QPushButton
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import time
if os.name == 'posix':        # if using OS X, open a special testing version of the program
    sys.path.append('/Users/rjf2/Documents/GitHub')
else:
    sys.path.append('C:\\Users\\Public\\Documents\\GitHub')
    sys.path.append('C:\\Users\\Robbie\\Documents\\GitHub')

from labAPI import gui, IO
import pandas as pd
import numpy as np

class AnalysisTab(gui.Tab):
    def __init__(self, panel, clock, name, filepath, excluded = []):
        super().__init__(name, panel)
        self.name = name
        self.filepath = filepath
        timecols = 2
        
        
        ''' Create canvas and navigation toolbar '''
        self.figure = plt.figure()
        self.figure.subplots_adjust(bottom=0.13, top=0.97, left=0.15, right=.95)

        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas, 1, 0, 2, 7)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        
        ''' Create combo box of plottable quantities '''
        with open(self.filepath, 'r') as file:
            self.watchpoints = IO.parseRow(file.readlines()[0])[timecols::]
        self.watchpoints = [x for x in self.watchpoints if x not in excluded]
        self.choicebox = self._addComboBox(self.watchpoints, 3, 0)
        self.choicebox.activated.connect(self.plot)
        
        self.plots = ['Histogram', 'Time series']
        self.plotbox = self._addComboBox(self.plots, 3, 1)
        self.plotbox.activated.connect(self.plot)
        
        ''' Create user options '''
        self.filter = 0
        self.filterCheckbox = self._addCheckbox('Remove outliers', 3, 2)

        ''' Create filename output '''
        self.fileLabel = self._addLabel(self.filepath, 3, 3, width = 4, fontsize = 'S')
        
    def plot(self):
        self.layout.addWidget(self.toolbar, 0, 0, 1, 2)
        if self.plotbox.currentText() == 'Histogram':
            self.histogram()
        elif self.plotbox.currentText() == 'Time series':
            self.timeSeries()
    
    def filter_outliers(self, data):
        for i in range(3):
            data = data[np.abs((data-data.mean())/data.std()) < 3]
        return data
    
    def read_data(self, choice):
        read = 0
        while not read:
            try:
                data = pd.read_csv(self.filepath,delimiter='\t',index_col = 0)[choice]
                read = 1
            except OSError:
                continue
        return data
    
    def histogram(self):
        choice = self.choicebox.currentText()
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        data = self.read_data(choice)
            
        ''' filter outliers '''
        if self.filterCheckbox.checkState():
            data = self.filter_outliers(data)

        ''' plot data '''
        ax = data.hist(figure=self.figure, ax=ax,bins=50)
#        ax.set_xlabel('%s (V)'%choice)
#        ax.set_ylabel('Counts')
        
        self.canvas.draw()
        
    def timeSeries(self):
        choice = self.choicebox.currentText()
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        data = self.read_data(choice)
        if self.filterCheckbox.checkState():
            data = self.filter_outliers(data)
        data.plot(ax=ax)
#        ax.set_xlabel('MJD')
#        ax.set_ylabel('%s (V)'%choice)
        
        self.canvas.draw()

        



    