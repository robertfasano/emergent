''' The Launcher offers a convenient way to start an EMERGENT session with the
    network, IP address, and port chosen from the GUI instead of passing these
    arguments in through the command line. When the user clicks the launch button,
    main.py is run with the specified parameters and the Launcher is closed.

    The GUI also offers default port suggestions by requesting an open port from
    the PC, as well as offering choice of IP address between the network card and
    localhost (for testing).
'''

import os
from PyQt5.QtGui import QFontDatabase, QIcon
from PyQt5.QtWidgets import (QWidget, QComboBox, QLabel, QHBoxLayout, QVBoxLayout,
                             QPushButton, QLineEdit)
from emergent.utilities.networking import get_address, get_open_port

class Launcher(QWidget):
    def __init__(self, app):
        QWidget.__init__(self)
        self.app = app
        self.setWindowIcon(QIcon('gui/media/icon.png'))

        QFontDatabase.addApplicationFont('gui/media/Exo2-Light.ttf')

        with open('gui/stylesheet.txt', "r") as file:
            self.setStyleSheet(file.read())

        self.setWindowTitle('EMERGENT')
        self.resize(325, 125)

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

        db_layout = QHBoxLayout()
        self.layout.addLayout(db_layout)
        db_layout.addWidget(QLabel('Database address'))
        self.db_edit = QLineEdit('3.17.63.193')
        db_layout.addWidget(self.db_edit)

        port_layout = QHBoxLayout()
        self.layout.addLayout(port_layout)
        port_layout.addWidget(QLabel('Port'))
        self.port_box = QLineEdit(str(get_open_port()))
        port_layout.addWidget(self.port_box)

        self.launch_button = QPushButton('Launch')
        self.launch_button.clicked.connect(self.launch)
        self.layout.addWidget(self.launch_button)

        self.show()

    def launch(self):
        ''' Start an EMERGENT session with settings from the GUI. '''
        network = self.network_box.currentText()
        address = self.addr_box.currentText()
        port = int(self.port_box.text())
        db_addr = self.db_edit.text()
        self.close()
        os.system('ipython -i main.py -- %s --addr %s --port %i --database_addr %s'%(network, address, port, db_addr))
