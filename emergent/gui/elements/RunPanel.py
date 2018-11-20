from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QHBoxLayout, QCheckBox, QTabWidget, QLineEdit, QSlider)
from PyQt5.QtCore import *
from emergent.archetypes.optimizer import Optimizer
from emergent.archetypes.parallel import ProcessHandler
from emergent.utility import list_algorithms, list_triggers
import inspect
import json
import logging as log
import time
from scipy.stats import linregress
import numpy as np
import datetime
import json

class RunLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent

        self.addWidget(self.parent.cost_box)
        self.parent.cost_box.currentTextChanged.connect(self.update_experiment)

        self.run_experimentParamsLayout = QVBoxLayout()
        self.cost_params_edit = QTextEdit('')
        self.run_experimentParamsLayout.addWidget(QLabel('Experiment parameters'))
        self.run_experimentParamsLayout.addWidget(self.cost_params_edit)
        self.addLayout(self.run_experimentParamsLayout)

        self.runIterationsLayout = QHBoxLayout()
        self.runIterationsLayout.addWidget(QLabel('Iterations'))
        self.runIterationsSlider = QSlider(Qt.Horizontal)
        self.runIterationsSlider.valueChanged.connect(self.updateIterations)
        self.runIterationsSlider.setRange(1,8)
        self.runIterationsSlider.setSingleStep(1)
        self.runIterationsLayout.addWidget(self.runIterationsSlider)
        self.runIterationsEdit = QLineEdit('')
        self.runIterationsLayout.addWidget(self.runIterationsEdit)
        self.runIterationsSlider.setValue(8)
        self.addLayout(self.runIterationsLayout)

        self.runDelayLayout = QHBoxLayout()
        self.runDelayLayout.addWidget(QLabel('Delay (ms)'))
        self.runDelayEdit = QLineEdit('0')
        self.runDelayLayout.addWidget(self.runDelayEdit)
        self.addLayout(self.runDelayLayout)

        self.runButtonsLayout = QHBoxLayout()
        self.runExperimentButton = QPushButton('Run')
        self.runExperimentButton.clicked.connect(self.start_experiment)
        self.runButtonsLayout.addWidget(self.runExperimentButton)
        self.stopExperimentButton = QPushButton('Stop')
        self.stopExperimentButton.clicked.connect(self.stop_experiment)
        self.runButtonsLayout.addWidget(self.stopExperimentButton)
        self.addLayout(self.runButtonsLayout)

        # self.runResultLayout = QHBoxLayout()
        # self.runResultLayout.addWidget(QLabel('Result'))
        # self.runResultEdit = QLineEdit('')
        # self.runResultLayout.addWidget(self.runResultEdit)
        # self.addLayout(self.runResultLayout)

    def get_settings_from_gui(self):
        settings = {}
        settings['cost_name'] = self.parent.cost_box.currentText()
        try:
            settings['control'] = self.parent.parent.treeWidget.get_selected_control()
        except IndexError:
            log.warn('Select inputs before starting optimization!')
            return
        params = self.cost_params_edit.toPlainText().replace('\n','').replace("'", '"')
        settings['params'] = json.loads(params)
        cost_params = self.cost_params_edit.toPlainText().replace('\n','').replace("'", '"')
        settings['cost_params'] = json.loads(cost_params)
        settings['iterations'] = self.runIterationsEdit.text()
        settings['delay'] = float(self.runDelayEdit.text())
        settings['callback'] = None

        return settings

    def run_experiment(self, control, experiment, cost_params, delay, iterations, optimizer, index, t, stopped = None):
        count = 0
        while not stopped():
            state = control.state
            result = experiment(state, params=cost_params)
            # self.runResultEdit.setText(str(result))
            # qApp.processEvents(QEventLoop.ExcludeUserInputEvents)
            count += 1
            time.sleep(delay/1000)
            if type(iterations) is int:
                if count >= iterations:
                    break
        control.optimizers[index]['status'] = 'Done'
        optimizer.log(t.replace(':','') + ' - ' + experiment.__name__)

    def start_experiment(self, *args, settings = {'callback': None, 'delay': None, 'iterations': None, 'control':None, 'cost_name': None, 'params': None, 'cost_params': None}):
        ''' Load any non-passed settings from the GUI '''
        gui_settings = self.get_settings_from_gui()
        print(settings)
        for s in settings:
            if settings[s] is None:
                settings[s] = gui_settings[s]
        iterations = settings['iterations']
        control = settings['control']
        experiment = getattr(control, settings['cost_name'])
        delay = settings['delay']
        cost_params = settings['cost_params']
        cost_params['cycles per sample'] = 1#int(self.cycles_per_sample_edit.text())

        optimizer, index = control.attach_optimizer(control.state, experiment)
        optimizer.sampler.initialize(control.state, experiment, None, cost_params)
        if iterations != 'Continuous':
            iterations = int(iterations)
        t = datetime.datetime.strftime(datetime.datetime.now(), '%H:%M')
        row = self.parent.parent.historyPanel.add_event(t, settings['cost_name'], None, 'Sampling', optimizer)
        self._run_thread(self.run_experiment, args = (control, experiment, cost_params, delay, iterations, optimizer, index, t))

    def stop_experiment(self):
        self._quit_thread(self.run_experiment)

    def updateIterations(self):
        try:
            val = self.runIterationsSlider.value()
            text = {}
            for i in range(1,8):
                text[i] = str(2**i)
            text[8] = 'Continuous'
            self.runIterationsEdit.setText(text[val])
        except AttributeError:
            return

    def update_experiment(self):
        ''' Read default params dict from source code and insert it in self.cost_params_edit. '''
        if self.parent.cost_box.currentText() is not '':
            try:
                control = self.parent.parent.treeWidget.get_selected_control()
            except IndexError:
                return
            f = getattr(control, self.parent.cost_box.currentText())
            args = inspect.signature(f).parameters
            args = list(args.items())
            for a in args:
                name = a[0]
                if name == 'params':
                    default = str(a[1])
                    if default == name:
                        default = 'Enter'
                    else:
                        default = default.split('=')[1]
                        default = default.replace('{', '{\n')
                        default = default.replace(',', ',\n')
                        default = default.replace('}', '\n}')
                        self.cost_params_edit.setText(default)
                        self.cost_params_edit.setText(default)
