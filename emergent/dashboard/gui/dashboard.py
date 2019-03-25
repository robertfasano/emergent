''' The MainWindow is the main window of EMERGENT, hosting panels imported from
    other modules in the emergent/gui/elements folder. '''

from flask import Flask
from flask_socketio import SocketIO, emit
import os
import psutil
from PyQt5.QtGui import QIcon, QFontDatabase
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QVBoxLayout, QPushButton,
                             QWidget, QMainWindow, QStatusBar, QMenuBar)
from PyQt5.QtCore import QTimer
from emergent.dashboard.gui import TaskPanel, NodeTree, ExperimentLayout#, GridWindow
from emergent.artiq.sequencer_grid import GridWindow
from emergent.utilities.signals import DictSignal
import requests
import pickle
import logging

class Dashboard(QMainWindow):
    def __init__(self, app, addr, port):
        QMainWindow.__init__(self)
        self.addr = addr
        self.port = port
        self.app = app
        ''' Set window style '''
        self.setWindowTitle('EMERGENT Dashboard')
        QFontDatabase.addApplicationFont('dashboard/gui/media/Exo2-Light.ttf')
        with open('dashboard/gui/stylesheet.txt', "r") as file:
            self.setStyleSheet(file.read())
        self.central_widget = QWidget()
        self.setWindowIcon(QIcon('../dashboard/gui/media/icon.png'))
        self.setCentralWidget(self.central_widget)
        layout = QHBoxLayout(self.central_widget)
        height = 720
        width = height*16/9

        self.resize(width, height)

        self.timestep_signal = DictSignal()
        self.actuate_signal = DictSignal()
        self.show_grid_signal = DictSignal()
        self.show_grid_signal.connect(self.show_grid)

        ''' Wait until connection is established '''
        self._connected = False
        while True:
            try:
                self.get('', format='raw')
                break
            except Exception:
                continue
        ''' Create QTreeWidget '''
        self.tree_layout = QVBoxLayout()
        self.tree_widget = NodeTree(self)
        self.tree_layout.addWidget(self.tree_widget)
        layout.addLayout(self.tree_layout)

        ''' Experiment interface '''
        self.experiment_layout = QVBoxLayout()
        layout.addLayout(self.experiment_layout)
        self.experiment_panel = ExperimentLayout(self)
        self.experiment_layout.addLayout(self.experiment_panel)

        ''' Create task panel '''
        self.task_panel = TaskPanel(self)
        self.experiment_layout.addLayout(self.task_panel)

        ''' Launch Flask socketIO server '''
        logging.getLogger('socketio').setLevel(logging.ERROR)
        logging.getLogger('engineio').setLevel(logging.ERROR)
        app = Flask(__name__)
        socketio = SocketIO(app, logger=False)

        @socketio.on('actuate')
        def actuate(state):
            self.actuate_signal.emit(state)

        @socketio.on('timestep')
        def update_timestep(step_name):
            self.timestep_signal.emit({'name': step_name})

        @socketio.on('sequencer')
        def show_grid(d):
            self.show_grid_signal.emit(d)

        @socketio.on('event')
        def event(event):
            self.task_panel.add_event(event)
        print('Starting flask-socketio server')
        from threading import Thread
        thread = Thread(target=socketio.run, args=(app,), kwargs={'port': 8000})
        thread.start()
        self.post('handshake', {'port': 8000})

    def get(self, url, format = 'json'):
        r = requests.get('http://%s:%s/'%(self.addr, self.port)+url)
        if format == 'json':
            return r.json()
        elif format == 'raw':
            return r.content
        elif format == 'pickle':
            return pickle.loads(r.content)

    def post(self, url, payload):
        requests.post('http://%s:%s/'%(self.addr, self.port)+url, json=payload)

    def show_grid(self, d):
        hub = d['hub']
        self.grid = GridWindow(self, hub)
        self.grid.show()
