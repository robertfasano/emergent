from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout, QLineEdit, QLabel, QComboBox, QTabWidget, QVBoxLayout, QApplication, QMenuBar, QAction
from PyQt5.QtGui import QFontDatabase, QFont
import json
import functools
import numpy as np
import os
#import monitorGUI

class SubMenu(QMenuBar):
    def __init__(self, parent=None):
        super(SubMenu, self).__init__(parent)
        self.setStyleSheet("""QMenuBar {
         background-color: transparent;
        }

     QMenuBar::item {
         background: transparent;
     }""")
        self.resize(320, 240)
        
class Tab(QWidget):
    def __init__(self, name, panel):
        super().__init__()
        self.loaded = 0
        self.panel = panel
        self.name = name
        self.maxRow = 0
        self.row = 0
        grid = QGridLayout()
        grid.setSpacing(10)
        self.layout = grid
        self.panel.tabs.addTab(self, self.name)
        
        self.settings = []
        self.widgets = {}
#        self.saveButton = self.addButton('Save', 'Save', self.save,self.maxRow+1,1, append=False)
#        self.loadButton = self.addButton('Load', 'Save', self.load,self.maxRow+1,2, append=False)


    def _addButton(self, title, label, function, row, col, width = 1, height = 1, args = None, append = False, style = 0):
        button = QPushButton(title)
        if args == None:
            button.clicked.connect(functools.partial(function))
        else:
            try:
                argWidgets = []
                for i in range(len(args)):
                    argWidgets.append(self.widgets[args[i]])
            except KeyError:
                argWidgets = args
            button.clicked.connect(functools.partial(function, tuple(argWidgets)))
        self.layout.addWidget(button, row, col, height, width)
        
        self.setLayout(self.layout)
        
        if append:
            self.maxRow = np.max([row, self.maxRow])
            self.settings.append({'type': 'button', 'title':title, 'label':label, 'row':row, 'col':col, 'args':args})
            self.widgets[label + 'Button'] = button
            self.repositionBottomRow()
        
        if style != 0:
            button.setStyleSheet(style)
        # the arguments themselves are not JSON serializable, so we store strings pointing towards the right boxes
        
        

        return button
    
    def _addLabel(self, title, row, col, width=1, height=1, style = 0):
        label = QLabel(title)
        self.layout.addWidget(label, row, col, height, width)
        self.setLayout(self.layout)
        
        self.settings.append({'type': 'label', 'title':title, 'row':row, 'col':col})
        self.widgets[title + 'Label'] = label
        self.maxRow = np.max([row, self.maxRow])
        if style != 0:
            label.setStyleSheet(style)
#        self.repositionBottomRow()

        return label
    
    def _addEdit(self, title, value, row, col, width=1, height=1):          
        edit = QLineEdit(value)
        self.layout.addWidget(edit, row, col, height, width)
        self.setLayout(self.layout)
        
        self.settings.append({'type': 'edit', 'title':title, 'value':value, 'row':row, 'col':col})
        self.widgets[title + 'Edit'] = edit
        self.maxRow = np.max([row, self.maxRow])
#        self.repositionBottomRow()

        return edit
    
    def addComboBox(self,title,items, row, col, currentText = None):
        box = QComboBox()
        for item in items:
            box.addItem(item)
        if currentText == None:
            currentText = items[0]
        box.setCurrentText(currentText)
        self.layout.addWidget(box, row, col)
        self.setLayout(self.layout)
        
        self.settings.append({'type': 'combo', 'title':title, 'items':items, 'row':row, 'col':col, 'text':currentText})
        self.widgets[title + 'Combo'] = box
        self.maxRow = np.max([row, self.maxRow])
        self.repositionBottomRow()

        return box
        
#    def _addUpdate(self, title, value, row = None, col=0, units = [], items=2):
#        if row == None:
#            row = self.row
#        self.addLabel(title, row, col)
#        edit = self.addEdit(title, str(value), row, col+1)
#        box = self.addComboBox(title, units, row, col+2)
#        button = self.addButton('Update', 'Update%s'%title, update, row, col+3, args=['%sEdit'%title, '%sCombo'%title])
#        self.row += 1
#        
#    def loadWidget(self, params):
#        if params['type'] == 'button':
#            self.addButton(params['title'], params['label'], update, params['row'], params['col'], args=params['args'])
#        elif params['type'] == 'label':
#            self.addLabel(params['title'], params['row'], params['col'])
#        elif params['type'] == 'edit':
#            self.addEdit(params['title'], params['value'], params['row'], params['col'])
#        elif params['type'] == 'combo':
#            self.addComboBox(params['title'], params['items'], params['row'], params['col'], currentText = params['text'])
#            
    def _save(self):
        print('Saving current parameters to file.')
        
        # update line edit values
        for widget in self.settings:
            if widget['type'] == 'edit':
                widget['value'] = self.widgets[widget['title']+'Edit'].text()
            elif widget['type'] == 'combo':
                widget['text'] = self.widgets[widget['title']+'Combo'].currentText()
        with open('./settings/%s.json'%self.name, 'w') as outfile:
            json.dump(self.settings, outfile)

    def _load(self):
        if self.loaded == 1:                # if just refreshing, then delete all widgets and recreate them
            for widget in self.widgets.values():
                self.layout.removeWidget(widget)
                widget.deleteLater()
            self.widgets = {}
            self.settings = []
        with open('./settings/%s.json'%self.name) as json_data:
            d = json.load(json_data)
        for widget in d:
            self.loadWidget(widget)
        self.loaded = 1
        

    
    def repositionBottomRow(self):
        self.layout.removeWidget(self.saveButton)
        self.saveButton.deleteLater()
        self.saveButton = self.addButton('Save', 'Load', self.save,self.maxRow+1,1, append=False)
        
        self.layout.removeWidget(self.loadButton)
        self.loadButton.deleteLater()
        self.loadButton = self.addButton('Load', 'Load', self.load,self.maxRow+1,2, append=False)
        
class Panel(QWidget):
    ''' add ___get_state___()? - compatibility with pickling '''
    def __init__(self, app, test = False):
        super().__init__()

        # create current directory

#        today = datetime.datetime.today()
#        dateString = today.strftime('%y%m%d')
#        self.directory = './%s/'%(dateString)
#        try:
#            os.stat(self.directory)
#        except:
#            os.mkdir(self.directory) 
#        self.filepath = '%s/logfile.txt'%(self.directory)

        self.processes = []
        
        # set style of child apps
        QFontDatabase.addApplicationFont('./meda/fonts/Roboto/Roboto-Light.ttf')
        self.color = 'red'
        self.font = {}
        self.font['S'] = QFont('Roboto', 10,weight=QFont.Light)
        self.font['M'] = QFont('Roboto', 16,weight=QFont.Light)
        self.font['L'] = QFont('Roboto', 24,weight=QFont.Light)
        self.styleSheet = "background-color:%s; color:white; border-width: 1px; border-radius: 5px;border-color: black; padding: 6px;"%self.color
        self.buttonStyle = "background-color:%s; color:white; border-width: 1px; border-radius: 5px;border-color:black; padding: 10px;"%'grey'
        self.buttonOnStyle = "background-color:%s; color:white; border-width: 20px; border-radius: 5px;border-color:black; padding: 10px;"%'green'
        self.buttonOffStyle = "background-color:%s; color:white; border-width: 20px; border-radius: 5px;border-color:black; padding: 10px;"%'red'
        self.styleAlarm = "background-color:%s; color:black; border-width: 20px; border-radius: 50px;border-color:black; padding: 10px;"%'yellow'
        self.styleUnlock = "background-color:%s; color:white; border-width: 20px; border-radius: 50px;border-color:black; padding: 10px;"%'red'
        self.styleLock = "background-color:%s; color:white; border-width: 20px; border-radius: 50px;border-color:black; padding: 10px;"%'green'

        self.initUI()                                   # create UI panel


    def exitApp(self):
        self.terminateProcesses()
        self.quit()
        
    def initUI(self):    
        ''' Generates the user interface layout and menu.
        '''
        # create main window with tabs
        self.setWindowTitle('Yb control panel')
        self.layout = QVBoxLayout(self)
        self.myQMenuBar = SubMenu()
        self.layout.addWidget(self.myQMenuBar)
        exitMenu = self.myQMenuBar.addMenu('File')
        exitAction = QAction('Exit', self)        
        exitAction.triggered.connect(self.exitApp)
        
        
        self.tabs = QTabWidget()

        # initialize each tab here
#        aomUnits = ['Hz', 'kHz', 'MHz']
#        self.aomTab = aomTab('AOM', self)
#        self.align399Tab = align399Tab('MEMS', self)
#        self.aomTab.load()

        
        
#        self.tabs.setCurrentIndex(0)            # sets default tab
#        self.tabs.setTabPosition(2)


        
    def loadTabs(self):
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        self.show()