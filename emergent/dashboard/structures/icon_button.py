from PyQt5.QtWidgets import QToolButton
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon

class IconButton(QToolButton):
    def __init__(self, filename, func):
        super().__init__()
        self.objectName = 'IconButton'
        self.setStyleSheet("IconButton{background-color: rgba(255, 255, 255, 0);border-style: outset; border-width: 0px;}");
        self.clicked.connect(func)
        self.setIcon(QIcon(filename))
        self.setIconSize(QSize(20,20))
