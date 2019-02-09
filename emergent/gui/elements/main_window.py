''' The MainWindow is the main window of EMERGENT, hosting panels imported from
    other modules in the emergent/gui/elements folder. '''

import os
import psutil
from PyQt5.QtGui import QIcon, QFontDatabase
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QVBoxLayout,
                             QWidget, QMainWindow, QStatusBar, QMenuBar)
from PyQt5.QtCore import QTimer
from emergent.gui.elements import ExperimentLayout, TaskPanel, NodeTree

class MainWindow(QMainWindow):
    def __init__(self, app, network):
        QMainWindow.__init__(self)
        self.network = network
        self.app = app
        ''' Set window style '''
        self.setWindowTitle('EMERGENT: %s @ %s:%s'%(network.name, network.addr, network.port))
        QFontDatabase.addApplicationFont('gui/media/Exo2-Light.ttf')
        with open('gui/stylesheet.txt', "r") as file:
            self.setStyleSheet(file.read())
        self.central_widget = QWidget()
        self.setWindowIcon(QIcon('gui/media/icon.png'))
        self.setCentralWidget(self.central_widget)
        layout = QHBoxLayout(self.central_widget)
        width = 960
        height = 720
        self.resize(width, height)

        ''' Create status bar '''
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.system_stats = QLabel()
        self.status_bar.addWidget(self.system_stats)
        self.get_system_stats()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.get_system_stats)
        self.timer.start(5*1000)

        ''' Create QTreeWidget '''
        self.tree_layout = QVBoxLayout()
        self.tree_widget = NodeTree(self.network, self)
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

        ''' Create menu bar '''
        self.menu_bar = QMenuBar()
        self.setMenuBar(self.menu_bar)
        self.network_menu = self.menu_bar.addMenu('Network')
        self.algorithm_menu = self.menu_bar.addMenu('Algorithm')
        self.experiment_menu = self.menu_bar.addMenu('Experiment')
        self.task_menu = self.menu_bar.addMenu('Tasks')

        self.create_menu_action(self.task_menu,
                                'Load task',
                                self.task_panel.load_task)
        self.create_menu_action(self.network_menu,
                                'Save state',
                                self.network.save)
        self.create_menu_action(self.algorithm_menu,
                                'Save parameters',
                                lambda: self.experiment_panel.save_params(self.experiment_panel.panel, 'algorithm'))
        self.create_menu_action(self.algorithm_menu,
                                'Reset parameters',
                                lambda: self.experiment_panel.update_algorithm_and_experiment(self.experiment_panel.panel, default=True, update_experiment=False))
        self.create_menu_action(self.experiment_menu,
                                'Save parameters',
                                lambda: self.experiment_panel.save_params(self.experiment_panel.panel, 'experiment'))
        self.create_menu_action(self.experiment_menu,
                                'Reset parameters',
                                lambda: self.experiment_panel.update_algorithm_and_experiment(self.experiment_panel.panel, default=True, update_algorithm=False))
        self.create_menu_action(self.algorithm_menu,
                                'Save default algorithm',
                                self.experiment_panel.save_default_algorithm)

    def create_menu_action(self, menu, name, function):
        ''' Add a new menu action to a menu. '''
        action = menu.addAction(name)
        action.triggered.connect(function)

    def get_system_stats(self):
        ''' Check memory and CPU usage and update status bar. '''
        mem = 'Memory usage: %.2f GB'%(psutil.Process(os.getpid()).memory_info()[0]/2.**30)
        cpu = 'CPU usage: %.2f%%'%psutil.cpu_percent()
        self.system_stats.setText(mem + '  |  ' + cpu)

    def setLayoutVisible(self, layout, visible):
        ''' Show or hide a layout and all of its child widgets. '''
        for i in range(layout.count()):
            w = layout.itemAt(i).widget()
            if w is not None:
                w.setVisible(visible)
            else:
                try:
                    self.setLayoutVisible(layout.itemAt(i), visible)
                except Exception as e:
                    print(e)
