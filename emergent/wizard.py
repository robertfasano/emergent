from PyQt5.QtWidgets import QApplication, QStyleFactory
from emergent.gui.elements import Creator
import sys

if __name__ == "__main__":
    QApplication.setStyle(QStyleFactory.create("Fusion"))
    app = QApplication(sys.argv)         # Create an instance of the application
    launcher = Creator(app)
    app.exec_()