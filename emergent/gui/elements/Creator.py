''' The Creator offers a graphical wizard for network creation, not only
    automatically setting up directory structure for a new network but also
    creating necessary scripts and allowing importing of templates.
'''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5.QtGui import QFontDatabase, QIcon
from PyQt5.QtWidgets import (QWidget, QComboBox, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit)
import os


class Creator(QWidget):
    def __init__(self, app):
        QWidget.__init__(self)
        self.app = app
        self.setWindowIcon(QIcon('gui/media/icon.png'))

        QFontDatabase.addApplicationFont('gui/media/Exo2-Light.ttf')

        with open('gui/stylesheet.txt',"r") as file:
            self.setStyleSheet(file.read())

        self.setWindowTitle('Network wizard')
        self.resize(325, 125)
        self.network_boxes = []

        self.layout = QVBoxLayout(self)


        name_layout = QHBoxLayout()
        self.layout.addLayout(name_layout)
        self.name_edit = QLineEdit()
        name_layout.addWidget(QLabel('Name'))
        name_layout.addWidget(self.name_edit)

        self.template_button = QPushButton('Add template')
        self.template_button.clicked.connect(self.add_template)
        self.layout.addWidget(self.template_button)

        self.create_button = QPushButton('Create')
        self.create_button.clicked.connect(self.create)
        self.layout.addWidget(self.create_button)

        self.show()

    def add_template(self):
        choice_layout = QHBoxLayout()
        self.layout.addLayout(choice_layout)
        choice_layout.addWidget(QLabel('Template'))
        self.network_boxes.append(QComboBox())
        import emergent.networks as nw
        for item in dir(nw):
            if '__' not in item:
                self.network_boxes[-1].addItem(item)
        # self.network_boxes[-1].currentTextChanged.connect(self.show_template)
        choice_layout.addWidget(self.network_boxes[-1])


    def create(self):
        templates = []
        for box in self.network_boxes:
            templates.append(box.currentText())
        name = self.name_edit.text()

        print('Created new network %s from templates %s.'%(name, templates))
        self.close()
        run_command = 'python new.py %s %s'%(name, templates)

        os.system(run_command)

    # def show_template(self):
    #     print(self.network_box.currentText())
