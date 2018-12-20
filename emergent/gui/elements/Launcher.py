#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
import sys
import types
from PyQt5.QtGui import QFontDatabase, QIcon
from PyQt5.QtWidgets import (QWidget, QComboBox, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QCheckBox)
from PyQt5.QtCore import *
import json
import os
import sys
from emergent.utility import get_address

class Launcher(QWidget):
    def __init__(self, app):
        QWidget.__init__(self)
        self.app = app
        self.setWindowIcon(QIcon('gui/media/icon.png'))

        QFontDatabase.addApplicationFont('gui/media/Exo2-Light.ttf')
        with open('gui/stylesheet.txt',"r") as file:
            self.setStyleSheet(file.read())
        self.setWindowTitle('EMERGENT')
        self.resize(250, 125)

        self.layout = QVBoxLayout(self)
        choice_layout = QHBoxLayout()
        self.layout.addLayout(choice_layout)

        choice_layout.addWidget(QLabel('Network'))
        self.network_box = QComboBox()
        for item in os.listdir('networks'):
            if '__' not in item:
                self.network_box.addItem(item)
        choice_layout.addWidget(self.network_box)

        addr_layout = QHBoxLayout()
        self.layout.addLayout(addr_layout)
        addr_layout.addWidget(QLabel('IP address'))
        self.addr_box = QComboBox()
        for item in [get_address(), '127.0.0.1']:
            self.addr_box.addItem(item)
        addr_layout.addWidget(self.addr_box)

        self.launch_button = QPushButton('Launch')
        self.launch_button.clicked.connect(self.launch)
        self.layout.addWidget(self.launch_button)

        self.show()

    def launch(self):
        network = self.network_box.currentText()
        address = self.addr_box.currentText()
        self.close()
        os.system('ipython -i main.py -- %s --addr %s'%(network, address))
