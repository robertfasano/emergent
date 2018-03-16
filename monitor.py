'''
    TODO: catch exception if user inputs blank value to a line edit (use last value)
          implement unlock last N points
          allow user to save parameter values
          add alarm reset time option in settings menu
    '''
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
    import winsound

from labAPI import gui, plotter, math, daq, IO, comms


class Watchpoint():
    ''' A Watchpoint object should be created for each variable you are monitoring. Upon initialization, this class generates
        GUI elements corresponding to the variable and checks that the Tab is connected to the corresponding ADC. The class also
        contains methods to check the state of the corresponding variable based on ADC measurements and comparisons to the setpoints.
        If mode = 'remote', live data is streamed over Dweet from a 'local' transmitter in the lab. '''
        
    def __init__(self, name, tab, params, row, col, mode = 'local', logic = 'mean'):
        self.tab = tab
        self.adc = params['ADC']
        self.mode = mode
        self.logic = logic
        if mode == 'remote':
            self.adc = {'type':'remote', 'id':self.tab.panel.guid}
        self.tab.connect_adc(self.adc)
        self.name = name
        self.params = params
        self.channel = params['Channel']
        self.label = self.tab._addButton(self.name, self.options, row, col, style = self.tab.panel.styleDynamic)
#        self.label = self.tab._addLabel(self.name, row, col, style = self.tab.panel.styleDynamic)

        self.label.setProperty('lock',0)
        
        self.value = self.tab._addEdit('0 V', row,col+1)
        self.lock = self.tab._addEdit(params['Unlock threshold'], row,col+2)
        self.alarm = self.tab._addEdit(params['Alarm threshold'], row,col+3)
        self.type = params['Type']
        self.tab.watchpoints[self.name] = self
        
        self.unlockedPoints = 0
        ''' Initialize behind-the-scenes options '''
        self.ADCOptions = dict((k,params[k]) for k in ['Type', 'Gate time (ms)', 'Channel'])
        self.settings = gui.Popup(self.name, self.ADCOptions)
        
    def options(self):
        self.settings.show()        
    
    def read_widget(self, widget, default = '1'):
        ''' Returns the value stored in a QLineEdit; if the widget is blank, returns default '''
        try:
            return widget.text()
        except ValueError:
            return default
        
    def state(self):
        ''' Get measurement parameters from gui.Popup item '''
        for param in self.ADCOptions:
            self.ADCOptions[param] = self.read_widget(self.settings.widgets[param])
        
        if self.mode == 'local':
            ''' Measure from ADC '''
            params = {'ADC':self.tab.ADCs[self.adc['id']], 'gate_time':self.ADCOptions['Gate time (ms)'], 'channel':self.channel}
            self.val = daq.measure(params, logic = self.logic)
            self.value.setText(math.convertUnits(self.val))
            
        elif self.mode == 'remote':
            self.val = self.tab.receiver[self.name]
            self.value.setText(math.convertUnits(self.val))
            
        ''' Perform logical lock/unlock state calculation and update tab '''
        self.alarmVal = math.convertUnits(self.read_widget(self.alarm))
        self.lockVal = math.convertUnits(self.read_widget(self.lock))
        
        sign = {'lower':1, 'upper':-1, 'range':-1}[self.type]
        if self.type == 'range':
            self.val = np.abs(self.val)
        if sign*(self.val - self.alarmVal) > 0:
            state = 1
            self.label.setStyleSheet(self.tab.panel.styleLock)
#            self.label.setProperty('lock',1)

        elif sign*(self.val - self.lockVal) > 0:
            state = -1   
            self.label.setStyleSheet(self.tab.panel.styleAlarm)
#            self.label.setProperty('lock',-1)

        else:
            self.unlockedPoints += 1
            if self.unlockedPoints >= self.tab.params['Points to unlock']:
                state = 0
            else:
                state = -1
            self.label.setStyleSheet(self.tab.panel.styleUnlock)
#            self.label.setProperty('lock',0)
#        self.label.style().unpolish(self.label)
#        self.label.style().polish(self.label)  
#        self.label.update()
#        self.label.setStyle(self.label.style())
#        self.tab.panel.app.processEvents()

        return self.val, state
    
class MonitorTab(gui.Tab):
    ''' The MonitorTab class fully implements a GUI-based data logger and viewer. Names and settings for each variable are read from
        a JSON file and the Watchpoint objects are created. Data is read from the Watchpoints when the user toggles the 'Saving' button,
        and lock/unlock decisions are handled logically. When unlocked, the clock must be manually relocked by toggling the 'Unlocked' 
        button into the 'Locked' state, where it will remain until an unlock signal is generated either from setpoint comparisons or 
        manual toggling. 
        
        If the MonitorTab is in mode = 'local', data is recorded from the ADC and broadcast over Dweet, where it can be read by additional
        MonitorTab objects in mode = 'remote'. In mode = 'local', the Tab also sends lock/unlock messages to a specified Slack webhook. 
        
        During data recording, two files are written in real time: logfile.txt, containing time series for all Watchpoints, and boolfile.txt,
        containing the logical state of each Watchpoint: 1 for lock, 0 for unlock, and -1 for warning (this last case is used to alert the
        operator of drifting levels before they trigger an unlock). '''
        
    def __init__(self, panel, clock, mode = 'local', TTL = None):
        super().__init__('Monitor', panel)
        self.TTL = TTL
        self.panel = panel
        self.clock = clock
        self.mode = mode
        self.panel.threads['Saving'] = 0
        self.TTLaddr = None
        self.TTLchannel = None
        self.offset = 2082844800 - 3437602072           # the offset from UNIX time defining the Yb timestamp
        self.dweet = comms.Dweet(self.panel.guid)
        
        ''' Initialize tracking dicts '''
        self.ADCs = {}
        
        ''' Initialize monitor state '''
        self.snooze = 0
        self.lock = 0
        self.day = datetime.datetime.today().day
        self.sync = 0

        ''' Generate UI '''
        self.load() 
        self.check()
        
        ''' Initialize remote variables '''
        if self.mode == 'remote':
            self.receiver = self.watchpoints.copy()
            for r in self.receiver:
                self.receiver[r] = 0
            self.receiver['Lock'] = 0
            
        ''' Create options menu '''
        menu = self.panel.myQMenuBar.addMenu('Monitor')
        saveAction = QAction('Save settings', self)        
        saveAction.triggered.connect(self.store)
        menu.addAction(saveAction)
        
        loadAction = QAction('Load settings', self)        
        loadAction.triggered.connect(self.recall)
        menu.addAction(loadAction)
        
    def alarm(self):
        while self.lock == 0:
            if not self.snooze:
                winsound.PlaySound('./media/alarm.wav', winsound.SND_FILENAME)
                time.sleep(15)

    def align(self):
        return
        
    def check(self):
        for wp in self.watchpoints.values():
            self.lock = self.lock and np.abs(wp.state())
            
    def connect_adc(self, adc):
        if adc['id'] not in self.ADCs:
            self.ADCs[adc['id']] = daq.connect(adc)
            print('Connected to %s with id %s.'%(adc['type'], adc['id']))
      
    def do_nothing(self):
        return
    
    def load(self):
        ''' Load watchpoints '''
        self.watchpoints = {}
        with open('monitorSettings_%i.json'%int(self.clock)) as json_data:
            d = json.load(json_data)
        col = 0
        for item in ['Value', 'Unlock level', 'Alarm level']:
            col += 1
            self._addLabel(item, 0, col)
        row = 1
        for ch in d.keys():
            if ch not in ['General', 'Blue probe TTL']:
                if ch == 'Blue probe':
                    Watchpoint(ch, self, d[ch], row, 0, mode = self.mode, logic='max')
                else:
                    Watchpoint(ch, self, d[ch], row, 0, mode = self.mode, logic='mean')
                row += 1
            if ch == 'General':
                self.params = d[ch]
        self.unlockedWatchpoint = None

        self.prepare_files()

        self.plotter = plotter.Plotter(self, 1, 4, row-1, 4, self.panel.filepath)

        ''' Create buttons '''
        self.saveButton = self._addButton('Not saving', self.save, row, 1, style = self.panel.styleUnlock)
        if self.mode == 'local':
            self.snoozeButton = self._addButton('Snooze off', self.toggle_snooze, row, 0, style = self.panel.styleLock)
            self.lockButton = self._addButton('Unlocked', self.update_lock, row, 2, style = self.panel.styleUnlock, args='toggle')
            self._addButton('Align', self.align, row, 3, style = self.panel.styleUnlock)
            
        if self.mode == 'remote':
            self.lockButton = self._addButton('Unlocked', self.do_nothing, row, 2, style = self.panel.styleUnlock)
        
        self.LED = self._addLED(row+1, 1, scale=0.25)

        self._setSpacing()
        
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
        
    def receive(self):
        while self.panel.threads['Receiving']:
            self.receiver = self.dweet.receive()
        
    def record(self):
        while self.panel.threads['Saving']:              
            ''' Check for day change and create new folder if necessary'''
            if datetime.datetime.today().day != self.day:
                self.day = datetime.datetime.today().day
                self.panel.prepare_filepath()
                self.prepare_files()
            
            self.LED.set_state(0)
            ''' Wait for TTL high '''
            
            params = {'ADC':self.ADCs[self.TTL], 'gate_time':1, 'channel':0}
            daq.TTL(params)
            self.LED.set_state(1)
            ''' Measure all watchpoints and update lock state'''
            vals = []
            params = []
            bools = []

            for wp in self.watchpoints.values():
                val, state = wp.state()
                params.append(wp.name)
                vals.append(val)
                bools.append(state)
                if not state and self.unlockedWatchpoint == None:
                    self.unlockedWatchpoint = wp.name
            if self.mode == 'local':
                prelock = self.lock
                self.lock = self.lock and all(bools)
                if prelock == 1 and self.lock == 0:
                    self.update_lock(state='off')
            elif self.mode == 'remote':
                if self.receiver['Lock'] != self.lock:
                    self.lock = self.receiver['Lock']
                    self.update_lock(state={1:'on',0:'off'}[self.lock])
            bools.append(self.lock)
            
            mjd = astropy.time.Time(datetime.datetime.today()).mjd
            ybTime = astropy.time.Time(mjd,format='mjd').unix + self.offset
            
            if self.mode == 'local':
                ''' Transmit dweet data '''
                self.dparams = params.copy()
                self.dparams.append('Lock')
                self.dvals = vals.copy()
                self.dvals.append(int(self.lock))
                self.dbools = bools.copy()
                self.sync = 1
                
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
                

            ''' TODO: is this wait necessary? '''
            time.sleep(1)
        
    def save(self):
        if self.panel.threads['Saving'] == 0:
            self.panel.threads['Saving'] = 1
            print('Starting data acquisition!')
            self.saveButton.setStyleSheet(self.panel.styleLock)
            self.saveButton.setText('Saving')
            self.thread = Thread(target=self.record)
            self.thread.start()
            
            if self.mode == 'local':
                self.panel.threads['Transmitting'] = 1
                self.transmitThread = Thread(target=self.transmit)
                self.transmitThread.start()
            elif self.mode == 'remote':
                self.panel.threads['Receiving'] = 1
                self.receiverThread = Thread(target=self.receive)
                self.receiverThread.start()  
                
        elif self.panel.threads['Saving'] == 1:
            self.panel.threads['Saving'] = 0
            print('Stopping data acquisition.')
            self.saveButton.setStyleSheet(self.panel.styleUnlock)
            self.saveButton.setText('Not saving')
            
            
            self.panel.threads['Transmitting'] = 0
            self.panel.threads['Receiving'] = 0
            
    def store(self):
        print('Saving monitor settings to file.')
    
    def toggle_snooze(self):
        self.snooze = (self.snooze + 1) % 2
        if not self.snooze:
            self.snoozeButton.setStyleSheet(self.panel.styleLock)
            self.snoozeButton.setText('Snooze off')
        else:
            self.snoozeButton.setStyleSheet(self.panel.styleUnlock)
            self.snoozeButton.setText('Snooze on')     
    
    def transmit(self):
        while self.panel.threads['Transmitting']:
            if self.sync == 1:
                self.dweet.send(self.dparams, self.dvals)
                self.sync = 0
        

    def update_lock(self, state):
        if state == 'toggle':
            state = {0: 'on', 1: 'off'}[self.lock]
            if state == 'off':
                self.unlockedWatchpoint = 'Manual'
                
        if state == 'on':
            print('Engaging lock.')
            self.lock = 1
            self.lockButton.setStyleSheet(self.panel.styleLock)
            self.lockButton.setText('Locked!')
            self.unlockedWatchpoint = None
            if self.mode == 'local':
                self.panel.slack.send('LOCKED')
            
            ''' Reset unlock counts of all watchpoints '''
            for wp in self.watchpoints.values():
                wp.unlockedPoints = 0
                
        elif state == 'off':
            print('Lock disengaged.')
            self.lock = 0
            self.lockButton.setStyleSheet(self.panel.styleUnlock)
            self.lockButton.setText('Unlocked.')
            
            if self.mode == 'local':
                self.panel.slack.send('UNLOCKED: %s'%self.unlockedWatchpoint)
                self.alarmThread = Thread(target=self.alarm)
                self.alarmThread.start()