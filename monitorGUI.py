'''
TODO: Add constant monitoring, but save only when a button is toggled. This will require a dedicated ADC that will not be shared with the autoAlign.
'''

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import functools
import numpy as np
import datetime
import pyqtgraph as pg
import json
import gui

class MonitorTab(gui.Tab):
    def __init__(self, panel):
        super().__init__('Monitor', panel)


#from clock import Edit, Label, Clickable

def triggerAlign(panel):
    if panel.alignBus['Aligning?'] == 0:
        panel.alignBus['Aligning?'] = 1
        panel.autoAlignButton.setStyleSheet(panel.buttonOnStyle)
        panel.autoAlignButton.setText('Aligning (click to stop)')
    elif panel.alignBus['Aligning?'] == 1:
        panel.alignBus['Aligning?'] = 0
        panel.autoAlignButton.setStyleSheet(panel.buttonOffStyle)
        panel.autoAlignButton.setText('autoAlign')
    return

def updateMonitorAlarm(panel):
    if panel.monitorAlarmOn == 1:
        panel.monitorAlarmOn = 0 
        panel.infoBus['Alarm?'] = 0
#        panel.monitorAlarmButton.setText('Alarm off')
#        panel.monitorAlarmButton.setStyleSheet(panel.buttonStyle)
        panel.alarmAction.setText('Turn alarm on')
    elif panel.monitorAlarmOn == 0:
        panel.monitorAlarmOn = 1 
        panel.infoBus['Alarm?'] = 1
#        panel.monitorAlarmButton.setText('Alarm on')
#        panel.monitorAlarmButton.setStyleSheet(panel.buttonOnStyle)
        panel.alarmAction.setText('Turn alarm off')

def snoozeMonitorAlarm(panel):
    if panel.infoBus['Snooze?'] == 1:
        panel.infoBus['Snooze?'] = 0
        panel.monitorAlarmButton.setStyleSheet(panel.buttonOnStyle)
        panel.monitorAlarmButton.setText('Alarm: Snooze off')
    elif panel.infoBus['Snooze?'] == 0:
        panel.infoBus['Snooze?'] = 1
        panel.monitorAlarmButton.setText('Alarm: Snooze on')
        panel.monitorAlarmButton.setStyleSheet(panel.buttonOffStyle)

def createTabForMonitor(panel):
        panel.plotChoice = 0                  # set default channel to display
        panel.timeOfLastUnlock = 0
        
        # read monitor settings from json file
    
        # create new Monitor tab
        grid = QGridLayout()
        grid.setSpacing(10)
        panel.tabMonitor.layout = grid        
        
        panel.tabMonitor.setLayout(panel.tabMonitor.layout)
        loadDefaultSettings(panel)

        panel.MonitorLabel = {}
        panel.MonitorValueEdit = {}
        panel.infoBus['Status'] = 'STATUS: Not connected.' 
        panel.infoBus['Debug'] = ''
        panel.infoBus['alarms'] = {}
        panel.infoBus['thresholds'] = {}
        panel.infoBus['avgTimes'] = {}
        monitorNum = 2
        for Monitor in panel.MonitorNames:
            panel.MonitorLabel[Monitor] = Label('CH%i: %s'%(monitorNum-1, Monitor), panel, style = panel.styleLock)
            panel.MonitorValueEdit[Monitor] = Edit('0.0', panel)
            
            if Monitor != 'Blue probe TTL':
                panel.tabMonitor.layout.addWidget(panel.MonitorValueEdit[Monitor], monitorNum, 1)
                panel.tabMonitor.layout.addWidget(panel.MonitorLabel[Monitor], monitorNum, 0)
            
                monitorNum += 1

        labelNum = 1
        for label in ['Value', 'Alarm threshold', 'Unlock threshold', 'Threshold type', 'Measurement time (ms)'
                    ]:
            panel.MonitorLabel[label] = Label(label, panel)

            panel.tabMonitor.layout.addWidget(panel.MonitorLabel[label], 1, labelNum)
            labelNum += 1

        # create unlock timer
        panel.lockStatusWidget = QLabel('LOCKED!')
        panel.lockStatusWidget.setFont(panel.font['M'])
#        panel.tabMonitor.layout.addWidget(panel.lockStatusWidget, len(panel.MonitorLabel), 0)
        
        panel.timeOfLastUnlockWidget = QLabel(' ')
        panel.timeOfLastUnlockWidget.setFont(panel.font['S'])
        panel.tabMonitor.layout.addWidget(panel.timeOfLastUnlockWidget, len(panel.MonitorLabel)+1, 1)
        
        # NIST logo
        pixmap = QPixmap('./media/NISTLogo.png')
        picLabel = QLabel('')
        picLabel.setPixmap(pixmap.scaled(75,75,aspectRatioMode=Qt.KeepAspectRatio))
        picLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        panel.tabMonitor.layout.addWidget(picLabel, len(panel.MonitorLabel)+1, labelNum+2)

        # create buttons for data logging, alarm control, etc
        panel.monitorAlarmOn = 0
        panel.infoBus['Alarm?'] = 1
        panel.infoBus['Snooze?'] = 1
        panel.monitorAlarmButton = Clickable('Alarm: Snooze on', panel, snoozeMonitorAlarm, panel)
        panel.monitorAlarmButton.setStyleSheet(panel.buttonOffStyle)
        panel.tabMonitor.layout.addWidget(panel.monitorAlarmButton, len(panel.MonitorLabel)-1, 0)
        
        # autoAlign controller
        panel.autoAlignButton = Clickable('autoAlign', panel, triggerAlign, panel)
        panel.autoAlignButton.setStyleSheet(panel.buttonOffStyle)
        panel.tabMonitor.layout.addWidget(panel.autoAlignButton, len(panel.MonitorLabel), 3)
        
        
        panel.monitorPlotButton = Clickable('Refresh', panel, panel.plotSelect, args=panel.plotChoice)
        panel.tabMonitor.layout.addWidget(panel.monitorPlotButton, len(panel.MonitorLabel)-1, labelNum+1)
        
        panel.resetUnlockTimerButton = Clickable('Unlocked', panel, panel.resetUnlockTimer)
        panel.resetUnlockTimerButton.setStyleSheet(panel.buttonOffStyle)
        panel.tabMonitor.layout.addWidget(panel.resetUnlockTimerButton, len(panel.MonitorLabel)-1, 2)
        
        panel.monitorLogging = 0
        panel.monitorLoggingButton = Clickable('Not saving',  panel, panel.startDataLogger)
        panel.monitorLoggingButton.setStyleSheet(panel.buttonOffStyle)
        panel.tabMonitor.layout.addWidget(panel.monitorLoggingButton, len(panel.MonitorLabel)-1, 1)
        
        # default settings buttons
        panel.monitorLoadDefaultSettingsButton = Clickable('Load default settings', panel, loadDefaultSettings, args=panel)
#        panel.tabMonitor.layout.addWidget(panel.monitorLoadDefaultSettingsButton, len(panel.MonitorLabel)-1, 3)
        
        panel.monitorSaveDefaultSettingsButton = Clickable('Save as default settings', panel, saveDefaultSettings, args=panel)
#        panel.tabMonitor.layout.addWidget(panel.monitorSaveDefaultSettingsButton, len(panel.MonitorLabel)-1, 4)
        
        # lock status
        panel.lockStatusWidget = QLabel('')
        panel.tabMonitor.layout.addWidget(panel.lockStatusWidget, len(panel.MonitorLabel), labelNum+1)
        
        # status text
        panel.monitorStatusWidget = QLabel(panel.infoBus['Status'])
        panel.tabMonitor.layout.addWidget(panel.monitorStatusWidget, len(panel.MonitorLabel), labelNum)

        # debug text
        panel.monitorDebugWidget = QLabel(panel.infoBus['Debug'])
        panel.tabMonitor.layout.addWidget(panel.monitorDebugWidget, len(panel.MonitorLabel), labelNum+1)

        # manual unlock button
        panel.manualUnlockEdit = QLineEdit('')
        panel.manualUnlockButton = Clickable('Manual unlock for last __ minutes', panel, panel.setUnlocked)
        panel.tabMonitor.layout.addWidget(panel.manualUnlockButton, len(panel.MonitorLabel)-1, 3)
        panel.tabMonitor.layout.addWidget(panel.manualUnlockEdit, len(panel.MonitorLabel)-1, 4)
        
        # discard N points line edit
        panel.discardEdit = QLineEdit('0')
#        panel.tabMonitor.layout.addWidget(panel.discardEdit, len(panel.MonitorLabel)-1, 5)
        
        # last lock/unlock status
        panel.lastLockLabel = QLabel('')
        panel.lastUnlockLabel = QLabel('')
        panel.tabMonitor.layout.addWidget(panel.lastLockLabel, len(panel.MonitorLabel), 0)
        panel.tabMonitor.layout.addWidget(panel.lastUnlockLabel, len(panel.MonitorLabel), 1)
        
        # optical comparison lock status
        panel.SrLockLabel = QLabel('Sr')
        panel.AlLockLabel = QLabel('Al+')
        panel.combLockLabel = QLabel('Comb')

        panel.SrLockLabel.setStyleSheet(panel.styleUnlock)
        panel.AlLockLabel.setStyleSheet(panel.styleUnlock)
        panel.combLockLabel.setStyleSheet(panel.styleUnlock)

#        panel.tabMonitor.layout.addWidget(panel.SrLockLabel, len(panel.MonitorLabel)+1, 4)
#        panel.tabMonitor.layout.addWidget(panel.AlLockLabel, len(panel.MonitorLabel)+1, 5)
#        panel.tabMonitor.layout.addWidget(panel.combLockLabel, len(panel.MonitorLabel)+1, 3)
        panel.tabMonitor.layout.addWidget(panel.SrLockLabel, 3, labelNum+2)
        panel.tabMonitor.layout.addWidget(panel.AlLockLabel, 2, labelNum+2)
        panel.tabMonitor.layout.addWidget(panel.combLockLabel, 1, labelNum+2)

        panel.checkLockButton = Clickable('Check lock settings', panel, panel.readJSONLock)
        panel.tabMonitor.layout.addWidget(panel.checkLockButton, len(panel.MonitorLabel)+1, 6)
        
        panel.fileLabel = QLabel('Not saving.')
        panel.tabMonitor.layout.addWidget(panel.fileLabel, len(panel.MonitorLabel)+1, 7)

        # plot instructions
#        panel.plotInfoWidget = QLabel('Left click + drag to zoom; right click to reset')
#        panel.tabMonitor.layout.addWidget(panel.plotInfoWidget, len(panel.MonitorLabel), labelNum)

        # monitor settings info
        panel.acqTimeWidget = QLabel('')
#        panel.tabMonitor.layout.addWidget(panel.acqTimeWidget, len(panel.MonitorLabel)+1, 0)

        # create dataPlotter
#        panel.resize(3500,100)
        panel.dataPlotterWindow = pg.GraphicsWindow(title="Basic plotting examples")
        pg.setConfigOptions(antialias=True)

        panel.tabMonitor.layout.addWidget(panel.dataPlotterWindow,1,labelNum,len(panel.MonitorNames)+1,2)
        panel.dataPlotterIsOpen = 1
        #undefined.QApplication.instance().exec_()           # weird behavior: scope will stream data as long as we call exec, even attached to an undefined variable
        
        panel.dataPlotterComboBox = QComboBox(panel)
        for item in panel.MonitorNames:
            if item == 'Blue probe TTL':
                        continue
            panel.dataPlotterComboBox.addItem(item)
#        panel.dataPlotterComboBox.activated.connect(panel.dataPlotterSelect)
        panel.dataPlotterComboBox.activated.connect(panel.plotSelect)

        panel.tabMonitor.layout.addWidget(panel.dataPlotterComboBox,len(panel.MonitorLabel)-1,labelNum)
        

def loadDefaultSettings(panel):
    with open('monitor/monitorSettings_Yb%i.json'%int(panel.clockNumber)) as json_data:
        d = json.load(json_data)
    panel.monitorSettings = d
    channels = []
    names = []
    for x in d:
        if x != 'General':
            channels.append(x)
            names.append(d[x]['name'])
    
    for x in d['General']:
        panel.settingsBus[x] = d['General'][x]
        
    panel.MonitorNames = names
    panel.MonitorAlarmThreshold = {}
    panel.MonitorUnlockThreshold = {}
    panel.MonitorThresholdType = {}
    panel.MonitorAveragingTime = {}
    for ch in channels:
        panel.MonitorAlarmThreshold[d[ch]['name']] = d[ch]['alarmThreshold']
        panel.MonitorUnlockThreshold[d[ch]['name']] = d[ch]['unlockThreshold']
        panel.MonitorThresholdType[d[ch]['name']] = d[ch]['type']
        panel.MonitorAveragingTime[d[ch]['name']] = d[ch]['avgTime']

    panel.MonitorAlarmThresholdEdit = {}
    panel.MonitorUnlockThresholdEdit = {}
    panel.MonitorThresholdTypeEdit = {}
    panel.MonitorAveragingTimeEdit = {}
    monitorNum = 2
    for Monitor in panel.MonitorNames:
        panel.MonitorAlarmThresholdEdit[Monitor] = Edit(panel.MonitorAlarmThreshold[Monitor], panel)
        panel.MonitorUnlockThresholdEdit[Monitor] = Edit(panel.MonitorUnlockThreshold[Monitor], panel)
        panel.MonitorThresholdTypeEdit[Monitor] = Edit(panel.MonitorThresholdType[Monitor], panel)
        panel.MonitorAveragingTimeEdit[Monitor] = Edit(panel.MonitorAveragingTime[Monitor], panel)
        panel.MonitorThresholdTypeEdit[Monitor].setReadOnly(True)
        if Monitor != 'Blue probe TTL':
            panel.tabMonitor.layout.addWidget(panel.MonitorAlarmThresholdEdit[Monitor], monitorNum, 2)
            panel.tabMonitor.layout.addWidget(panel.MonitorUnlockThresholdEdit[Monitor], monitorNum, 3)
            panel.tabMonitor.layout.addWidget(panel.MonitorThresholdTypeEdit[Monitor], monitorNum, 4)
            panel.tabMonitor.layout.addWidget(panel.MonitorAveragingTimeEdit[Monitor], monitorNum, 5)
        
        
            monitorNum += 1
        
           
def saveDefaultSettings(panel):
    d = panel.monitorSettings
    for ch in d:
        d[ch]['alarmThreshold'] = panel.MonitorAlarmThresholdEdit[d[ch]['name']].text()
        d[ch]['unlockThreshold'] = panel.MonitorUnlockThresholdEdit[d[ch]['name']].text()
        d[ch]['avgTime'] = panel.MonitorAveragingTimeEdit[d[ch]['name']].text()
        
    with open('monitor/monitorSettings_Yb%i.json'%int(panel.clockNumber), 'w') as outfile:
        json.dump(d, outfile)
        
class Clickable(QPushButton):
    def __init__(self, name, panel, function, args = None):
        super().__init__()
        self.setText(name)
        if args == None:
            self.clicked.connect(functools.partial(function))
        else:
            self.clicked.connect(functools.partial(function, args))
        self.setStyleSheet(panel.buttonStyle)
        
class Label(QLabel):
    def __init__(self, name, panel, style = None):
        super().__init__()
        self.setText(name)
        if not style == None:
            self.setStyleSheet(style)
        self.setFont(panel.font['S'])
        
class Edit(QLineEdit):
    def __init__(self, name, panel):
        super().__init__()
        self.setText(name)
        self.setFont(panel.font['S'])
        

    
