from PyQt5.QtWidgets import QWidget, QPushButton, QGridLayout, QLineEdit, QLabel, QComboBox, QTabWidget, QVBoxLayout, QMenuBar, QAction
from PyQt5.QtGui import QFontDatabase, QFont
import json
import functools
import numpy as np

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
    def __init__(self, name, params, watchpoint):
        super().__init__()
        self.params = params
        self.setWindowTitle('%s options'%name)
        grid = QGridLayout()
        grid.setSpacing(10)
        self.layout = grid
        
        self.populate()
        
        self.saveButton = QPushButton('Save')
        self.layout.addWidget(self.saveButton, 0, 2)
        
       
    def populate(self):
        row = 0
        for key in self.params:
            label = QLabel(key)    
            self.layout.addWidget(label, row, 0)
            edit = QLineEdit(self.params[key])    
            self.layout.addWidget(edit, row, 1)
            row += 1
        self.setLayout(self.layout)
        
        
class Tab(QWidget):
    def __init__(self, name, panel):
        super().__init__()
        self.panel = panel
        self.name = name
        self.layout = QGridLayout()
        self.layout.setSpacing(10)
        self.panel.tabs.addTab(self, self.name)
        

    def _addButton(self, label, function, row, col, width = 1, height = 1, args = None, style = 0):
        button = QPushButton(label)
        if args == None:
            button.clicked.connect(functools.partial(function))
        else:
            button.clicked.connect(functools.partial(function, args))
        self.layout.addWidget(button, row, col, height, width)
        
        self.setLayout(self.layout)
        
        if style != 0:
            button.setStyleSheet(style)
        
        

        return button
    
    def _addLabel(self, label, row, col, width=1, height=1, style = 0):
        label = QLabel(label)
        self.layout.addWidget(label, row, col, height, width)
        self.setLayout(self.layout)
        
        if style != 0:
            label.setStyleSheet(style)

        return label
    
    def _addEdit(self, label, row, col, width=1, height=1):          
        edit = QLineEdit(label)
        self.layout.addWidget(edit, row, col, height, width)
        self.setLayout(self.layout)
        
        return edit
    
    def _addComboBox(self,items, row, col, currentText = None):
        box = QComboBox()
        for item in items:
            box.addItem(item)
        if currentText == None:
            currentText = items[0]
        box.setCurrentText(currentText)
        self.layout.addWidget(box, row, col)
        self.setLayout(self.layout)
        
        return box
        
        
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

        self.threads = {}
        
        # set style of child apps
        QFontDatabase.addApplicationFont('./meda/fonts/Roboto/Roboto-Light.ttf')
        self.color = 'red'
        self.font = {}
        self.font['S'] = QFont('Roboto', 10,weight=QFont.Light)
        self.font['M'] = QFont('Roboto', 16,weight=QFont.Light)
        self.font['L'] = QFont('Roboto', 24,weight=QFont.Light)
        self.styleSheet = "background-color:%s; color:white; border-width: 1px; border-radius: 5px;border-color: black; padding: 6px;"%self.color
        self.styleAlarm = "background-color:%s; color:black;  border-radius:5px; padding: 10px;"%'yellow'
        self.styleUnlock = "background-color:%s; color:white; border-radius:5px; padding: 10px;"%'red'
        self.styleLock = "background-color:%s; color:white; border-radius:5px; padding: 10px;"%'green'
        
        self.filepath = None
        self.initUI()                                   # create UI panel


    def exitApp(self):
        for thread in self.threads:
            self.threads[thread] = 0
        self.quit()
        
    def initUI(self):    
        ''' Generates the user interface layout and menu.
        '''
        # create main window with tabs
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