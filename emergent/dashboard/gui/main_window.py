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
    def __init__(self, app, client, server):
        QMainWindow.__init__(self)
        self.client = client
        self.network = client.get_state()
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

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.sync)
        self.connection_params = {'sync delay': 0.25}
        self.update_timer.start(self.connection_params['sync delay']*1000)

        ''' Experiment interface '''
        self.experiment_layout = QVBoxLayout()
        layout.addLayout(self.experiment_layout)

        ''' Create task panel '''
        self.task_panel = TaskPanel(self)
        self.experiment_layout.addLayout(self.task_panel)

    def sync(self):
        ''' Queries each connected client for the state of its Network, then updates
            the NetworkPanel to show the current state of the entire network. '''
        try:
            network = self.client.get_state()
        except ConnectionRefusedError:
            self.update_timer.stop()
            log.warning('Connection refused by server at %s:%i.', client.addr, client.port)
        self.tree_widget.generate(network)
