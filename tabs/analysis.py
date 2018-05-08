import os
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QFileDialog
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from threading import Thread
if os.name == 'posix':        # if using OS X, open a special testing version of the program
    sys.path.append('/Users/rjf2/Documents/GitHub')
else:
    sys.path.append('C:\\Users\\Public\\Documents\\GitHub')
    sys.path.append('C:\\Users\\Robbie\\Documents\\GitHub')

from scipy.optimize import curve_fit
from labAPI import IO
from labAPI.gui import gui
import pandas as pd
import numpy as np
import allantools

class AnalysisTab(gui.Tab):
    def __init__(self, panel, clock, name, filepath, columns = [], excluded = []):
        super().__init__(name, panel)
        self.name = name
        self.filepath = filepath
        timecols = 2
        self.columns = columns
        self.panel = panel
        ''' Create canvas and navigation toolbar '''
        self.figure = plt.figure()
        self.figure.subplots_adjust(bottom=0.13, top=0.95, left=0.15, right=.95)

        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas, 1, 0, 2, 7)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        
        ''' Create combo box of plottable quantities '''
        if self.columns == []:
            with open(self.filepath, 'r') as file:
                self.watchpoints = IO.parseRow(file.readlines()[0])[timecols::]
        else:
            self.watchpoints = self.columns
        self.watchpoints = [x for x in self.watchpoints if x not in excluded]
        self.choicebox = self._addComboBox(self.watchpoints, 3, 0)
        self.choicebox.activated.connect(self.plot)
        
        self.plots = ['Histogram', 'Time series']
        if self.name == 'Performance':
            self.plots.append('Allan deviation')
        self.plotbox = self._addComboBox(self.plots, 3, 1)
        self.plotbox.activated.connect(self.plot)
        
        ''' Create user options '''
        self.filterCheckbox = self._addCheckbox(3, 2, name='Remove outliers')
        self.averageCheckbox = self._addCheckbox(3,3, name='1-hour averaging')
        
        ''' Create filename output and explore option '''
        self.fileLabel = self._addLabel(self.parse_filestring(self.filepath), 3, 5, width = 3, fontsize = 'S')
        self.fileButton = self._addButton('Change', self.change_directory, 3, 4, icon = './media/folder.png')
        
    def parse_filestring(self, path):
        return '../'+path.split(self.panel.folder)[-1]
        
    def change_directory(self):
        folder = '/'.join(self.filepath.split('/')[0:-1])
        filename = QFileDialog.getOpenFileName(None, 'Choose file', folder)[0]
        if filename != '':
            self.filepath = self.parse_filestring(filename)
            self.fileLabel.setText(self.filepath)
        
    def plot(self):
        self.layout.addWidget(self.toolbar, 0, 0, 1, 2)
        if self.plotbox.currentText() == 'Histogram':
            self.histogram()
        elif self.plotbox.currentText() == 'Time series':
            self.timeSeries()
        elif self.plotbox.currentText() == 'Allan deviation':
            self.allan_deviation()
    
    def plot_thread(self):
        self.threadPlot = Thread(target=self.plot)
        self.threadPlot.start()
        
    def remove_outliers(self, data):
        for i in range(3):
            data = data[np.abs((data-data.mean())/data.std()) < 3]
        return data
    
    def read_data(self, choice):
        read = 0
        while not read:
            try:
                if self.columns == []:
                    data = pd.read_csv(self.filepath,delimiter='\t',index_col = 0)[choice]
                else:
                    data = pd.read_csv(self.filepath,delimiter='\t',names = self.columns)[choice]
                read = 1
            except OSError:
                continue
        if self.filterCheckbox.checkState():
            data = self.remove_outliers(data)
        
        return data
    
    def histogram(self):
        choice = self.choicebox.currentText()
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        data = self.read_data(choice)
        ax = data.hist(figure=self.figure, ax=ax,bins=50)
#        ax.set_xlabel('%s (V)'%choice)
#        ax.set_ylabel('Counts')
        
        self.canvas.draw()
        
    def timeSeries(self):
        choice = self.choicebox.currentText()
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        data = self.read_data(choice)
        
        if self.averageCheckbox.checkState():
            window = int(3600/np.mean(np.diff(data.index.values)))
            mean = data.rolling(window=window).mean()
            std = data.rolling(window=window).std()
            lower = mean-std
            upper = mean+std
            
            ax.plot(mean, 'k')
            ax.plot(lower, '--k')
            ax.plot(upper, '--k')
        else:
            data.plot(ax=ax)
#        ax.set_xlabel('MJD')
#        ax.set_ylabel('%s (V)'%choice)
        
        self.canvas.draw()
        
    def power_law(self, tau, a):
        return a/np.sqrt(tau)
    
    def allan_deviation(self):
        choice = self.choicebox.currentText()
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        data = self.read_data(choice)
        
        ''' Compute and plot overlapping Allan deviation using allantools package '''
        (t2, ad, ade, adn) = allantools.oadev(data.values, rate=1/np.mean(np.diff(data.index.values)), data_type="freq", taus='octave')
        ax.errorbar(t2, ad, yerr=ade, fmt='.k',)
        ax.grid(which='major', linewidth = 1)
        ax.grid(which='minor', linewidth = 0.5)
        ax.set_xscale('log')
        ax.set_yscale('log')
        
        

        ''' Fit line and plot '''
        first_point = 100
        tau = t2[np.where(t2>first_point)]
        dev = ad[np.where(t2>first_point)]
        popt, pcov = curve_fit(self.power_law, tau, dev)
        
        fit = self.power_law(t2, popt[0])
        ax.plot(t2, fit, 'k')
        
        ax.text(0.75,0.75, '$\sigma_y={:.2e}'.format(popt[0]) +'/\sqrt{\\tau}$', fontsize=12, transform = ax.transAxes, bbox=dict(facecolor='white', edgecolor='black', pad=10.0))
        self.canvas.draw()

        
def filter_data(df, window=3600):
    mean = df.rolling(window=window).mean()
    std = df.rolling(window=window).std()
    lower = mean-std
    upper = mean+std
    
    plt.plot(mean, 'k')
    plt.plot(lower, '--k')
    plt.plot(upper, '--k')



    