import json
import sys
import os
import numpy as np
import time
from threading import Thread
import astropy.time
import datetime
from PyQt5.QtWidgets import QAction
if os.name == 'posix':        # if using OS X, open a special testing version of the program
    sys.path.append('/Users/rjf2/Documents/GitHub')
else:
    sys.path.append('C:\\Users\\Public\\Documents\\GitHub')
    sys.path.append('C:\\Users\\Robbie\\Documents\\GitHub')

from labAPI import gui, plotter, math, daq, IO

class Watchpoint():
    def __init__(self, name, tab, params, row, col):
        self.adc = params['ADC']
        self.tab = tab
        self.name = name
        self.params = params
        self.channel = params['Channel']
        self.label = self.tab._addButton(self.name, self.options, row, col, style = self.tab.panel.styleLock)

        self.value = self.tab._addEdit('0 V', row,col+1)
        self.lock = self.tab._addEdit(params['Unlock threshold'], row,col+2)
        self.alarm = self.tab._addEdit(params['Alarm threshold'], row,col+3)
        self.type = params['type']
        self.tab.watchpoints[self.name] = self
        
        ''' Initialize behind-the-scenes options '''
        hiddenOptions = dict((k,params[k]) for k in ['type', 'Averaging time (ms)', 'ADC'])
        self.settings = gui.Popup(self.name, hiddenOptions, self)
        
    def options(self):
        self.settings.show()        
        
    def update(self, val):
        return
    
    def state(self):
        self.val = daq.measure(self.adc, self.channel)
        self.value.setText(math.convertUnits(self.val))
        self.alarmVal = math.convertUnits(self.alarm.text())
        self.lockVal = math.convertUnits(self.lock.text())
        
        sign = {'lower':1, 'upper':-1, 'range':-1}[self.type]
        if self.type == 'range':
            self.val = np.abs(self.val)
        if sign*(self.val - self.alarmVal) > 0:
            state = 1
            self.label.setStyleSheet(self.tab.panel.styleLock)
        elif sign*(self.val - self.lockVal) > 0:
            state = -1   
            self.label.setStyleSheet(self.tab.panel.styleAlarm)
        else:
            state = 0
            self.label.setStyleSheet(self.tab.panel.styleUnlock)
        return self.val, state
        
    
class MonitorTab(gui.Tab):
    def __init__(self, panel, clock):
        super().__init__('Monitor', panel)
        self.panel = panel
        self.clock = clock
        self.panel.threads['Saving'] = 0
        self.lock = 0
        self.TTLaddr = None
        self.TTLchannel = None
        self.offset = 2082844800 - 3437602072           # the offset from UNIX time defining the Yb timestamp

        
        ''' Generate UI '''
        self.load() 
        self.check()
        
        ''' Create options menu '''
        menu = self.panel.myQMenuBar.addMenu('Monitor')
        saveAction = QAction('Save settings', self)        
        saveAction.triggered.connect(self.store)
        menu.addAction(saveAction)
        
        loadAction = QAction('Load settings', self)        
        loadAction.triggered.connect(self.recall)
        menu.addAction(loadAction)
        
        
    def align(self):
        return
        
    def check(self):
        for wp in self.watchpoints.values():
            self.lock = self.lock and np.abs(wp.state())
            
    def load(self):
        self.watchpoints = {}
        with open('monitorSettings_%i.json'%int(self.clock)) as json_data:
            d = json.load(json_data)
        col = 0
        for item in ['Value', 'Alarm threshold', 'Unlock threshold']:
            col += 1
            self._addLabel(item, 0, col)
        row = 1
        for ch in d.keys():
            if ch not in ['General', 'Blue probe TTL']:
                Watchpoint(ch, self, d[ch], row, 0)
                row += 1
                
        self.prepare_files()

        self.plotter = plotter.Plotter(self, 1, len(self.watchpoints)+1, row-1, 2, self.panel.filepath)

        ''' Create buttons '''
        self._addButton('Snooze', self.snooze, row, 0, style = self.panel.styleLock)
        self.saveButton = self._addButton('Not saving', self.save, row, 1, style = self.panel.styleUnlock)
        self.lockButton = self._addButton('Unlocked', self.update_lock, row, 2, style = self.panel.styleUnlock, args='toggle')
        self._addButton('Align', self.align, row, 3, style = self.panel.styleUnlock)
        
    def prepare_files(self):
        if os.path.isfile(self.panel.filepath): 
            self.logfile = open(self.panel.filepath, 'a')
            self.boolfile = open(self.panel.filepath.replace('log','bool'), 'a')
        else:
            self.logfile = open(self.panel.filepath, 'w')
            header = ['MJD', 'Timestamp']
            header.extend(list(self.watchpoints.keys()))
            self.logfile.write(IO.formatRow(header, newline='none'))
            self.logfile.flush()
            
            self.boolfile = open(self.panel.filepath.replace('log','bool'), 'w')
            header.append('Human')
            self.boolfile.write(IO.formatRow(header, newline='none'))
            self.boolfile.flush()
    
    def recall(self):
        print('Loading monitor settings from file.')
        
    def record(self):
        while self.panel.threads['Saving']:
            daq.TTL(self.TTLaddr, self.TTLchannel)
            params = []
            vals = []
            bools = []
            for wp in self.watchpoints.values():
                val, state = wp.state()
                params.append(wp.name)
                vals.append(val)
                bools.append(state)
            prelock = self.lock
            self.lock = self.lock and all(bools)
            if prelock == 1 and self.lock == 0:
                self.update_lock(state='off')
            bools.append(self.lock)
            mjd = astropy.time.Time(datetime.datetime.today()).mjd
            ybTime = astropy.time.Time(mjd,format='mjd').unix + self.offset
            

            ''' Format and write log string '''
            decs = [7, 3]
            lengths = [12, 12]
            decs.extend([6]*len(self.watchpoints))
            lengths.extend([7]*len(self.watchpoints))
            lst = [mjd, ybTime]
            lst.extend(vals)
            logString = IO.formatRow(lst, newline = 'start',decs=decs, lengths=lengths)
            self.logfile.write(logString)
            self.logfile.flush()
            
            ''' Format and write bool string '''
            decs = [7, 3]
            lengths = [12, 12]
            decs.extend([0]*(len(self.watchpoints)+1))
            lengths.extend([1]*(len(self.watchpoints)+1))
            lst = [mjd, ybTime]
            lst.extend(bools)
            boolString = IO.formatRow(lst, newline = 'start', decs = decs, lengths = lengths)
            self.boolfile.write(boolString)
            self.boolfile.flush()

            time.sleep(1)
                
    def save(self):
        if self.panel.threads['Saving'] == 0:
            self.panel.threads['Saving'] = 1
            print('Starting data acquisition!')
            self.saveButton.setStyleSheet(self.panel.styleLock)
            self.saveButton.setText('Saving.')
            self.thread = Thread(target=self.record)
            self.thread.start()
        elif self.panel.threads['Saving'] == 1:
            self.panel.threads['Saving'] = 0
            print('Stopping data acquisition.')
            self.saveButton.setStyleSheet(self.panel.styleUnlock)
            self.saveButton.setText('Not saving.')


    def snooze(self):
        return
    
    def store(self):
        print('Saving monitor settings to file.')
    
    def update_lock(self, state):
        if state == 'toggle':
            state = {0: 'on', 1: 'off'}[self.lock]
        if state == 'on':
            print('Engaging lock.')
            self.lock = 1
            self.lockButton.setStyleSheet(self.panel.styleLock)
            self.lockButton.setText('Locked!')
        elif state == 'off':
            print('Lock disengaged.')
            self.lock = 0
            self.lockButton.setStyleSheet(self.panel.styleUnlock)
            self.lockButton.setText('Unlocked.')



