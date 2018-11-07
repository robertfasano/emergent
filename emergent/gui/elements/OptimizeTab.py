from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QHBoxLayout, QCheckBox, QTabWidget, QLineEdit, QSlider)
from PyQt5.QtCore import *

class OptimizeTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        optimizeTabLayout = QVBoxLayout()
        self.setLayout(optimizeTabLayout)
        parent.algorithm_box = QComboBox()
        optimizeTabLayout.addWidget(parent.algorithm_box)
        paramsLayout = QHBoxLayout()
        optimizerParamsLayout = QVBoxLayout()
        parent.params_edit = QTextEdit('')
        optimizerParamsLayout.addWidget(QLabel('Algorithm parameters'))
        optimizerParamsLayout.addWidget(parent.params_edit)
        paramsLayout.addLayout(optimizerParamsLayout)
        experimentParamsLayout = QVBoxLayout()
        parent.cost_params_edit = QTextEdit('')
        experimentParamsLayout.addWidget(QLabel('Experiment parameters'))
        experimentParamsLayout.addWidget(parent.cost_params_edit)
        paramsLayout.addLayout(experimentParamsLayout)
        optimizeTabLayout.addLayout(paramsLayout)
        plotLayout = QHBoxLayout()
        parent.cycles_per_sample_edit = QLineEdit('1')
        parent.cycles_per_sample_edit.setMaximumWidth(100)
        plotLayout.addWidget(QLabel('Cycles per sample'))
        plotLayout.addWidget(parent.cycles_per_sample_edit)
        optimizeTabLayout.addLayout(plotLayout)
        parent.parent.treeWidget.itemSelectionChanged.connect(parent.update_control)
        parent.algorithm_box.currentTextChanged.connect(parent.update_algorithm)
        parent.cost_box.currentTextChanged.connect(parent.update_experiment)
        optimizeButtonsLayout = QHBoxLayout()
        parent.optimizer_button = QPushButton('Go!')
        parent.optimizer_button.clicked.connect(parent.prepare_optimizer)
        optimizeButtonsLayout.addWidget(parent.optimizer_button)
        optimizeTabLayout.addLayout(optimizeButtonsLayout)
        parent.progress_bar = QProgressBar()
        parent.progress_bar.setTextVisible(False)
        parent.max_progress = 100
        parent.progress_bar.setMaximum(parent.max_progress)
        optimizeTabLayout.addWidget(parent.progress_bar)
