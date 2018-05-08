from PyQt5.QtWidgets import QCheckBox, QWidget, QPushButton, QGridLayout, QLineEdit, QLabel, QComboBox, QTabWidget, QVBoxLayout, QMenuBar, QAction
from PyQt5.QtGui import QFontDatabase, QFont, QPixmap, QIcon
from PyQt5.QtCore import QSize, Qt
import datetime
import functools
import os
from threading import Thread

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
       

class Popup(QWidget):
    ''' A popup for managing less-used options not displayed on the front panel of a Tab. If a function is passed, a button appears to start this function in a new thread.'''
    def __init__(self, name, params, function = None):
        super().__init__()
        self.params = params
        self.function = function
        self.setWindowTitle('%s options'%name)
        grid = QGridLayout()
        grid.setSpacing(10)
        self.layout = grid
        
        self.populate()
        
        self.saveButton = QPushButton('Save')
        self.layout.addWidget(self.saveButton, 0, 2)
          
    def populate(self):
        self.widgets = {}
        row = 0
        for key in self.params:
            label = QLabel(key)    
            self.layout.addWidget(label, row, 0)
            edit = QLineEdit(str(self.params[key]))   
            self.layout.addWidget(edit, row, 1)
            self.widgets[key] = edit
            row += 1
        self.setLayout(self.layout)
        
        if self.function != None:
            self.button = QPushButton('Start')
            self.button.clicked.connect(self.start)
            self.layout.addWidget(self.button)
            
    def start(self):
        self.update_parameters()
        thread = Thread(target = self.function, args = (self.params.values()))
        thread.start()

    def update_parameters(self):    
        for key in self.params:
            x = self.widgets[key].text()
            if key != 'filename':
                x = float(x)
            self.params[key] = x
            
class LED(QLabel):
    ''' A simple on/off LED whose state can be toggled with the set_state() function '''
    def __init__(self, scale=1):
        super().__init__('')
        self.scale = scale
        self.setPixmap(QPixmap('./media/led-red-on.png').scaled(self.scale*100, self.scale*100))
        self.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)

    def set_state(self, i):
        if i == 1:
            self.setPixmap(QPixmap('./media/led-blue-on.png').scaled(self.scale*100, self.scale*100))
        elif i == 0:
            self.setPixmap(QPixmap('./media/led-red-on.png').scaled(self.scale*100, self.scale*100))
            
class ToggleButton(QPushButton):
    def __init__(self, panel, width=1, height=1):
        super().__init__()
        self.state = 0
        self.panel = panel
        self.setStyleSheet(self.panel.styleGray)
        self.clicked.connect(self.toggle)
        size = panel.gridSize
        self.setFixedSize(size.scaled(size.width()*width, size.height()*height, 0))
    def toggle(self):
        self.state = (self.state + 1) % 2
        if self.state == 1:
            self.setStyleSheet(self.panel.styleYellow)
        else:
            self.setStyleSheet(self.panel.styleGray)
            
class Tab(QWidget):
    ''' The Tab class is a higher-level version of the tab objects stored by a QTabWidget. This class aims to streamline and 
        standardize creation of tabs and their respective GUI elements to enable efficient development.    
    '''
    def __init__(self, name, panel, subtab = False):
        super().__init__()
        self.panel = panel
        if subtab:
            self.tab = panel
            if self.tab.tabs == None:
                self.tab.tabs = QTabWidget()
            self.panel = panel.panel
            
        self.name = name
        self.filepath = {}
        self.layout = QGridLayout()
        self.layout.setSpacing(10)
        if not subtab:
            self.panel.tabs.addTab(self, self.name)
            self.setLayout(self.layout)

        else:
            self.tab.tabs.addTab(self, self.name)
            self.tab.layout.addWidget(self.tab.tabs)
            self.setLayout(self.layout)
            self.tab.setLayout(self.tab.layout)



    
    def _setSpacing(self):
        ''' Fix size of grid rows, columns '''
        for row in range(self.layout.rowCount()):
            self.layout.setRowStretch(row, 1)
        for col in range(self.layout.columnCount()):
            self.layout.setColumnStretch(col, 1)
        self.setLayout(self.layout)

    def _addButton(self, label, function, row, col, width = 1, height = 1, args = None, style = 0, icon = None):
        button = QPushButton(label)
        if args == None:
            button.clicked.connect(functools.partial(function))
        else:
            button.clicked.connect(functools.partial(function, args))
        self.layout.addWidget(button, row, col, height, width)
        
        self.setLayout(self.layout)
        
        if style != 0:
            button.setStyleSheet(style)
            
        if not icon == None:
            button.setIcon(QIcon(icon))
            button.setText('')
            
        button.setFont(self.panel.font['S'])
        size = self.panel.gridSize
        button.setFixedSize(size.scaled(size.width()*width, size.height()*height, 0))

        return button

    def _addCheckbox(self, row, col, name = None):
        if name == None:
            checkbox = QCheckBox()
        else:
            checkbox = QCheckBox(name)
        self.layout.addWidget(checkbox, row, col)
        self.setLayout(self.layout)
        
        return checkbox
    
    def _addComboBox(self,items, row, col, currentText = None, width=1, height=1):
        box = QComboBox()
        for item in items:
            box.addItem(item)
        if currentText == None:
            currentText = items[0]
        box.setCurrentText(str(currentText))
        self.layout.addWidget(box, row, col)
        self.setLayout(self.layout)
        box.setFont(self.panel.font['S'])
        
        size = self.panel.gridSize
        box.setFixedSize(size.scaled(size.width()*width, size.height()*height, 0))

        return box

    def _addEdit(self, label, row, col, width=1, height=1):          
        edit = QLineEdit(str(label))
        self.layout.addWidget(edit, row, col, height, width)
        self.setLayout(self.layout)
        edit.setFont(self.panel.font['S'])
        
        size = self.panel.gridSize
        edit.setFixedSize(size.scaled(size.width()*width, size.height()*height, 0))
        return edit
    
    def _addLabel(self, label, row, col, width=1, height=1, style = 0, size = 'default', fontsize = 'M', centered = False):
        label = QLabel(str(label))
        self.layout.addWidget(label, row, col, height, width)
        self.setLayout(self.layout)
        
        if style != 0:
            label.setStyleSheet(style)
            
        label.setFont(self.panel.font[fontsize])
        
        size = self.panel.gridSize
        label.setFixedSize(size.scaled(size.width()*width, size.height()*height, 0))
        
        if centered:
            label.setAlignment(Qt.AlignVCenter)
            
        return label
    
    def _addLED(self, row, col, scale=1):
        led = LED(scale=scale)
        self.layout.addWidget(led, row, col)
        self.setLayout(self.layout)
        
        return led

    def _addToggleButton(self, row, col, width = 1, height = 1):
        button = ToggleButton(self.panel)
        self.layout.addWidget(button, row, col, height, width)
        self.setLayout(self.layout)
        
#    def _addUpdate(self, title, items, row, col):
#        ''' A multi-widget consisting of a row of items, each containing a QLabel name, QLineEdit value, QComboBox units; after all items, add a QPushButton '''
#        
    def _addUpdate(self, title, func, row, col, items = [], values = [], channels = [], units = [[]]):
        widgets = []
        widgets.append(self._addLabel(title, row, col))
        widgets.append(self._addComboBox(channels, row, col+1))
        j = 2
        for i in range(len(items)):
            widgets.append(self._addEdit(str(values[i]), row, col+j))
            widgets.append(self._addComboBox(units[i], row, col+j+1))
            j += 3
#        button = self.addButton('Update', 'Update%s'%title, self.updateAOM, row, col+j+2, args=['%sEdit'%title, '%sCombo'%title])
        widgets.append(self._addButton('Update', self.updateAOM, row, col+j+2, args=widgets))

        return widgets
        
        


class Panel(QWidget):
    ''' The Panel class is the central GUI element hosting multiple Tabs for different tasks. '''
    def __init__(self, app, clock, folder, subfolder = '', mode = 'local'):
        super().__init__()
        print('Creating panel')
        self.mode = mode
        self.threads = {}
        self.folder = folder
        self.subfolder = subfolder
        self.app = app
        self.filepath = {}

        self.threads = {}
        
        ''' Placeholder for remote communications - should initialize in child object '''
        self.slack = None
        self.guid = None
        
        ''' Define styles for child apps '''
        QFontDatabase.addApplicationFont('./media/fonts/Roboto/Roboto-Light.ttf')
        self.color = 'red'
        self.font = {}
        self.font['S'] = QFont('Roboto', 10,weight=QFont.Light)
        self.font['M'] = QFont('Roboto', 16,weight=QFont.Light)
        self.font['L'] = QFont('Roboto', 24,weight=QFont.Light)
        
        self.styleButton = ''
        self.styleAlarm = "background-color:%s; color:black;  border-width:10px; border-radius:5px; padding: 10px;"%'yellow'
        self.styleUnlock = "background-color:%s; color:white;  border-width:10px; border-radius:5px; padding: 10px;"%'red'
        self.styleLock = "background-color:%s; color:white;  border-width:10px; border-radius:5px; padding: 10px;"%'green'
        self.styleDynamic = """ QPushButton[lock='0'] {background-color:red; color:white; border-width: 20px; border-radius:50px; border-color:black; padding:10px;}
                                QPushButton[lock='1'] {background-color:green; color:white; border-width: 20px; border-radius:50px; border-color:black; padding:10px;}
                                QPushButton[lock='-1'] {background-color:yellow; color:black; border-width: 20px; border-radius:50px; border-color:black; padding:10px;}"""

        self.styleGray = "background-color:%s; color:white;  border-width:10px; padding: 10px;"%'gray'
        self.styleYellow = "background-color:%s; color:white;  border-width:10px; padding: 10px;"%'yellow'

        self.gridSize = QSize(120,40)
        
        self.guid = None
        self.prepare_filepath()
        self.initUI()                                   # create UI panel
    def exitApp(self):
        for thread in self.threads:
            self.threads[thread] = 0
        self.quit()
        
    def initUI(self):    
        ''' Generates the user interface layout and menu. '''
        self.layout = QVBoxLayout(self)
        self.myQMenuBar = SubMenu()
        self.layout.addWidget(self.myQMenuBar)
#        fileMenu = self.myQMenuBar.addMenu('File')
#        exitAction = QAction('Exit', self)        
#        exitAction.triggered.connect(self.exitApp)
#        fileMenu.addAction(exitAction)
        
        self.tabs = QTabWidget()
    
#        self.tabs.setCurrentIndex(0)            # sets default tab
#        self.tabs.setTabPosition(2)

    def loadTabs(self):
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        self.show()
        
    def prepare_filepath(self):
        ''' Create file directory for the current day'''
        today = datetime.datetime.today().strftime('%y%m%d')
        self.directory = self.folder + today + '/' + self.subfolder

        for d in [self.folder + today, self.directory]:
            try:
                os.stat(d)
            except:
                os.mkdir(d) 
        self.filepath['Monitor'] = self.directory
        if self.mode == 'local':
            self.filepath['Monitor'] += '/logfile.txt'
        elif self.mode == 'remote':
            self.filepath['Monitor'] += '/remote_logfile.txt'    
