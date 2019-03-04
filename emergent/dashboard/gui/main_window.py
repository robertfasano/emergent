''' The MainWindow is the main window of EMERGENT, hosting panels imported from
    other modules in the emergent/gui/elements folder. '''

import os
import psutil
from PyQt5.QtGui import QIcon, QFontDatabase
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QVBoxLayout,
                             QWidget, QMainWindow, QStatusBar, QMenuBar)
from PyQt5.QtCore import QTimer
from emergent.dashboard.gui import TaskPanel, NodeTree

class Dashboard(QMainWindow):
    def __init__(self, app, p2p):
        QMainWindow.__init__(self)
        self.p2p = p2p
        from emergent.protocols.p2p import DashAPI
        self.p2p.api = DashAPI(self)
        self.network = self.p2p.send({'op': 'get', 'target': 'state'})['value']

        self.app = app
        ''' Set window style '''
        self.setWindowTitle('EMERGENT Dashboard')
        QFontDatabase.addApplicationFont('gui/media/Exo2-Light.ttf')
        with open('gui/stylesheet.txt', "r") as file:
            self.setStyleSheet(file.read())
        self.central_widget = QWidget()
        self.setWindowIcon(QIcon('../gui/media/icon.png'))
        self.setCentralWidget(self.central_widget)
        layout = QHBoxLayout(self.central_widget)
        height = 720
        width = height*16/9

        self.resize(width, height)


        ''' Create QTreeWidget '''
        self.tree_layout = QVBoxLayout()
        self.tree_widget = NodeTree(self.network, self)
        self.tree_layout.addWidget(self.tree_widget)
        layout.addLayout(self.tree_layout)

        ''' Experiment interface '''
        self.experiment_layout = QVBoxLayout()
        layout.addLayout(self.experiment_layout)