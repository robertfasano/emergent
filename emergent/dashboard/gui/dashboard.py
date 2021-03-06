''' The MainWindow is the main window of EMERGENT, hosting panels imported from
    other modules in the emergent/gui/elements folder. '''

from flask import Flask
from flask_socketio import SocketIO, emit
import os
import psutil
from PyQt5.QtGui import QIcon, QFontDatabase
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QVBoxLayout, QPushButton,
                             QWidget, QMainWindow, QStatusBar, QMenuBar, QFrame)
from PyQt5.QtCore import QTimer
from emergent.dashboard.gui import TaskPanel, NodeTree, ExperimentLayout, GridWindow
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

        ''' Define Qt signals '''
        self.timestep_signal = DictSignal()
        self.sequence_update_signal = DictSignal()
        self.test_signal = DictSignal()
        self.actuate_signal = DictSignal()
        self.show_grid_signal = DictSignal()
        self.show_grid_signal.connect(self.show_grid)
        self.plot_signal = DictSignal()
        self.plot_signal.connect(self.plot_window)
        ''' Wait until connection is established '''
        self._connected = False
        while True:
            try:
                self.get('', format='raw')
                break
            except Exception:
                continue
        ''' Load modules '''

        ''' Create QTreeWidget '''
        frame = QFrame()
        layout.addWidget(frame)
        self.tree_layout = QVBoxLayout()
        frame.setLayout(self.tree_layout)

        self.tree_widget = NodeTree(self)
        self.tree_layout.addWidget(self.tree_widget)
        button_layout = QHBoxLayout()
        self.tree_layout.addLayout(button_layout)
        from emergent.dashboard.structures.icon_button import IconButton
        button_layout.addWidget(IconButton('dashboard/gui/media/Material/content-save-outline.svg', lambda: self.post('save'), tooltip='Save device states'))
        button_layout.addWidget(IconButton('dashboard/gui/media/Material/content-undo.svg', lambda: self.post('load'), tooltip='Load device states'))
        lock_button = IconButton('dashboard/gui/media/Material/baseline-lock-open.svg',
                                 self.tree_widget.lock,
                                 tooltip='Load device states',
                                 toggle_icon='dashboard/gui/media/Material/baseline-lock-closed.svg')
        button_layout.addWidget(lock_button)
        button_layout.addStretch()
        button_layout.addWidget(IconButton('dashboard/gui/media/Material/outline-timer.svg', self.show_grid, tooltip='Open timing grid'))

        ''' Experiment interface '''
        self.experiment_layout = QVBoxLayout()
        layout.addLayout(self.experiment_layout)
        self.experiment_panel = ExperimentLayout(self)
        self.experiment_layout.addLayout(self.experiment_panel)

        self.test_signal.connect(self.experiment_panel.pipeline_panel.add_block)

        ''' Create task panel '''
        self.task_panel = TaskPanel(self)
        self.experiment_layout.addLayout(self.task_panel)

        ''' Open reverse connection to master '''
        logging.getLogger('socketio').setLevel(logging.ERROR)
        logging.getLogger('engineio').setLevel(logging.ERROR)
        app = Flask(__name__)
        socketio = SocketIO(app, logger=False)

        @socketio.on('actuate')
        def actuate(state):
            self.actuate_signal.emit(state)

        @socketio.on('plot')
        def plot(data):
            self.plot_signal.emit(data)

        @socketio.on('timestep')
        def update_timestep(d):
            self.timestep_signal.emit({'name': d['name']})

        @socketio.on('sequencer')
        def show_grid(d):
            self.show_grid_signal.emit(d)

        @socketio.on('sequence update')
        def update_sequence():
            self.sequence_update_signal.emit({})

        @socketio.on('sequence reorder')
        def update_sequence_order(d):
            knob = self.tree_widget.get_knob('hub', 'sequencer', d['name'])
            knob.move(d['n'])

        @socketio.on('event')
        def event(event):
            self.task_panel.add_event(event)
        print('Starting flask-socketio server')
        from threading import Thread
        thread = Thread(target=socketio.run, args=(app,), kwargs={'port': self.port+1})
        thread.start()
        self.post('handshake', {'port': self.port+1})

        @socketio.on('test')
        def test(d):
            self.test_signal.emit(d)

    def get(self, url, request = {}, format = 'json'):
        r = requests.get('http://%s:%s/'%(self.addr, self.port)+url)
        if format == 'json':
            return r.json()
        elif format == 'raw':
            return r.content
        elif format == 'pickle':
            return pickle.loads(r.content)

    def post(self, url, payload={}):
        requests.post('http://%s:%s/'%(self.addr, self.port)+url, json=payload)

    def show_grid(self, d={}):
        print(type(self.get('artiq/connected')))
        if self.get('artiq/connected')==1:
            self.grid = GridWindow(self)
            self.grid.show()
        else:
            print('No sequencer connected.')

    def plot_window(self, data):
        from emergent.pipeline.plotting import PlotWindow
        self.plot_window = PlotWindow(data)

    def create_menu_action(self, menu, name, function):
        ''' Add a new menu action to a menu. '''
        action = menu.addAction(name)
        action.triggered.connect(function)
