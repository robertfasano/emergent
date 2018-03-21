import time
import json
from PyQt5.QtWidgets import QWidget, QTabWidget
from labAPI import gui


            
class TimingTab(gui.Tab):
    def __init__(self, panel):
        super().__init__('Timing', panel)
        self.panel = panel
        self.filename = self.panel.filepath['Timing']
        self.tabs = None
        self.tab = {}
        for name in ['A', 'B', 'C']:
            self.tab[name] = gui.Tab(name, self, subtab = True)

        
#        self.layout.addWidget(self.tabs)

        self.generate_grid()
#        self._addButton('Load', self.get_timing, self.rows+2, 0)
#        self._addButton('Save', self.get_timing, self.rows+2, 1)

    def generate_grid(self):
        j = self.get_timing()
        self.rows = 16
        self.cols = 30
        for name in ['A', 'B', 'C']:            
            for row in range(1,self.rows+1):
                self.tab[name]._addLabel(name+str(row-1), row, 0, fontsize='S', centered=True)
            for col in range(1,self.cols+1):
                self.tab[name]._addEdit('0',0, col)
            for row in range(1,self.rows+1):
                for col in range(1,self.cols+1):
                    self.tab[name]._addToggleButton(row, col)
                
            self.tab[name].layout.setSpacing(0)
        
            
        
    def get_timing(self):
        ''' Reads a timing sequence from a json file exported by the Labview timing controller '''
        with open(self.filename) as data:
            j = json.load(data)
        return j



#j = get_timing('O:/Public/Yb clock/pyClock2.0/timing.json')