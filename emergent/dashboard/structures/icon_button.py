from PyQt5.QtWidgets import QToolButton
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon, QPixmap

class IconButton(QToolButton):
    def __init__(self, filename, func, tooltip='', toggle_icon=None):
        super().__init__()
        self.objectName = 'IconButton'
        self.setStyleSheet("IconButton{background-color: rgba(255, 255, 255, 0);border-style: outset; border-width: 0px;}");
        if func is not None:
            self.clicked.connect(func)
        self.icon = QIcon(filename)
        self.setIcon(self.icon)
        self.setIconSize(QSize(20,20))
        self.setPopupMode(2)
        self.setToolTip(tooltip)

        if toggle_icon is not None:
            self.toggleIcon = QIcon(toggle_icon)
            self.setCheckable(True)
            self.clicked.connect(self.update_icon)

    def update_icon(self):
        if self.isChecked():
            self.setIcon(self.toggleIcon)
        else:
            self.setIcon(self.icon)
