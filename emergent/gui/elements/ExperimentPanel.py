from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QHBoxLayout, QCheckBox, QTabWidget, QLineEdit, QSlider)
from PyQt5.QtCore import *
from emergent.gui.elements import OptimizeLayout, ServoLayout, RunLayout
from emergent.archetypes.parallel import ProcessHandler
import inspect
import json
import logging as log
import time
from scipy.stats import linregress
import numpy as np
import datetime
import __main__
import os
import importlib
from utility import list_errors, list_experiments


class ExperimentLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent
        self.tabWidget = QTabWidget()
        self.addWidget(self.tabWidget)
        self.current_control = None
        self.parent.treeWidget.itemSelectionChanged.connect(self.update_control)

        ''' Create Optimizer tab '''
        optimizeTab = QWidget()
        self.optimizePanel = OptimizeLayout(self)
        optimizeTab.setLayout(self.optimizePanel)
        self.tabWidget.addTab(optimizeTab, 'Optimize')

        ''' Create Servo tab '''
        servoTab = QWidget()
        self.servoPanel = ServoLayout(self)
        servoTab.setLayout(self.servoPanel)
        self.tabWidget.addTab(servoTab, 'Servo')

        ''' Create Run tab '''
        runTab = QWidget()
        self.runPanel = RunLayout(self)
        runTab.setLayout(self.runPanel)
        self.tabWidget.addTab(runTab, 'Run')

    def get_default_params(self, name, panel):
        inst = self.get_algorithm(name, panel)
        params = inst.params
        algo_params = {}
        for p in params:
            algo_params[p] = params[p].value

        return algo_params

    def load_module(self, panel):
        if panel.name == 'Optimize':
            module = importlib.__import__('optimizers')
        else:
            module = importlib.__import__('servos')
        return module

    def get_algorithm(self, name, panel):
        module = self.load_module(panel)
        return getattr(module, name)()

    def get_description(self, panel, algo_name, parameter):
        params = self.get_algorithm(algo_name, panel).params
        return params[parameter].description


    def list_algorithms(self, panel):
        module = self.load_module(panel)
        names = []
        for a in dir(module):
            if '__' not in a:
                inst = getattr(module, a)
                names.append(inst().name)
        return names


    def file_to_dict(self, algo, experiment, param_type, panel, default = False):
        ''' Generates parameter suggestions for either the algorithm or experiment
            params, based on the choice of param_type. '''

        ''' Look for relevant parameters in the json file in the network's params directory '''
        network_name = __main__.network_path.split('.')[2]
        control = self.parent.treeWidget.currentItem().root

        if not os.path.exists('./networks/%s/params/'%network_name):
            os.mkdir('./networks/%s/params/'%network_name)
        params_filename = './networks/%s/params/'%network_name + '%s.%s.txt'%(control.name, experiment.__name__)
        if not default:
            try:
                ''' Load params from file '''
                with open(params_filename, 'r') as file:
                    params = json.load(file)


                ''' Make sure the current algorithm's parameters are contained '''
                if param_type == 'algorithm':
                    if algo.name in params['algorithm']:
                        return params['algorithm'][algo.name]
                    else:
                        d = self.get_default_params(algo.name, panel)
                        with open(params_filename, 'r') as file:
                            params = json.load(file)
                        params['algorithm'][algo.name] = d
                        with open(params_filename, 'w') as file:
                            json.dump(params, file)
                        return d
                else:
                    if 'cycles per sample' not in params['experiment']:
                        params['experiment']['cycles per sample'] = 1
                    return params['experiment']

            except OSError:
                pass
        ''' If file does not exist, then load from introspection '''
        params = {'experiment': {}, 'algorithm': {}}
        if param_type == 'algorithm':
            params['algorithm'][algo.name] = {}

        ''' load experiment params '''
        args = inspect.signature(experiment).parameters
        args = list(args.items())
        for a in args:
            if a[0] != 'params':
                continue
            d = str(a[1]).split('=')[1]
            d = json.loads(d.replace("'", '"'))
        params['experiment'] = d

        if param_type == 'algorithm':
            params['algorithm'][algo.name] = self.get_default_params(algo.name, panel)

        with open(params_filename, 'w') as file:
            json.dump(params, file)

        if param_type == 'algorithm':
            return params['algorithm'][algo.name]
        else:
            if 'cycles per sample' not in params['experiment']:
                params['experiment']['cycles per sample'] = 1
            return params['experiment']

    def save_params(self, panel, param_type, params = None):
        ''' param_type: 'experiment' or 'algorithm' '''
        network_name = __main__.network_path.split('.')[2]
        control = self.parent.treeWidget.currentItem().root
        algorithm_name = panel.algorithm_box.currentText()

        experiment = getattr(control, panel.cost_box.currentText())
        params_filename = './networks/%s/params/'%network_name + '%s.%s.txt'%(control.name, experiment.__name__)

        ''' Pull params from gui '''
        if params is None:
            f = {'algorithm': panel.apl.get_params(), 'experiment': lambda: panel.epl.get_params()}[param_type]
            params = f()

        ''' Load old params from file '''
        with open(params_filename, 'r') as file:
            old_params = json.load(file)

        ''' Update old params with new values and save to file '''
        for p in params:
            if param_type == 'experiment':
                old_params[param_type][p] = params[p]
            else:
                old_params[param_type][algorithm_name][p] = params[p]
        with open(params_filename, 'w') as file:
            json.dump(old_params, file)

    def update_control_panel(self, panel, exp_or_error, algo):
        ''' Updates the algorithm box with the methods available to the currently selected control. '''
        control = self.parent.treeWidget.currentItem().root
        if algo:
            panel.algorithm_box.clear()
            if exp_or_error == 'experiment':
                for item in self.list_algorithms(panel):
                    panel.algorithm_box.addItem(item.replace('_',' '))
                    panel.algorithm_box.setCurrentText('GridSearch')
            elif exp_or_error == 'error':
                for item in self.list_algorithms(panel):
                    panel.algorithm_box.addItem(item.replace('_',' '))
        if exp_or_error == 'error':
            panel.cost_box.clear()
            for item in list_errors(control):
                panel.cost_box.addItem(item)
        elif exp_or_error == 'experiment':
            panel.cost_box.clear()
            for item in list_experiments(control):
                panel.cost_box.addItem(item)

    def update_control(self):
        control = self.parent.treeWidget.currentItem().root
        if control == self.current_control:
            return
        else:
            self.current_control = control
        self.update_control_panel(self.optimizePanel, 'experiment', True)
        self.update_algorithm_and_experiment(self.optimizePanel)
        self.update_control_panel(self.runPanel, 'experiment', False)
        self.update_experiment(self.runPanel)
        self.update_control_panel(self.servoPanel, 'error', True)
        self.update_algorithm_and_experiment(self.servoPanel)

    def update_experiment(self, panel):
        ''' Read default params dict from source code and insert it in self.cost_params_edit. '''
        if panel.cost_box.currentText() is '':
            return
        control = self.parent.treeWidget.currentItem().root
        experiment = getattr(control, panel.cost_box.currentText())
        d = self.file_to_dict(experiment, experiment, 'experiment', panel)
        panel.epl.set_parameters(d)

    def update_algorithm_and_experiment(self, panel, default = False, update_algorithm = True, update_experiment = True):
        if panel.cost_box.currentText() is '':
            return
        if panel.algorithm_box.currentText() is '':
            return
        control = self.parent.treeWidget.currentItem().root
        try:
            experiment = getattr(control, panel.cost_box.currentText())
        except AttributeError:
            return
        if update_algorithm:
            algo_name = panel.algorithm_box.currentText()
            algo = self.get_algorithm(algo_name, panel)
            algo_params = self.file_to_dict(algo, experiment, 'algorithm', panel, default = default)
            panel.apl.set_parameters(algo_params)

        if update_experiment:
            exp_params = self.file_to_dict(experiment, experiment, 'experiment', panel, default = default)
            panel.epl.set_parameters(exp_params)

    def start_process(self, *args, process = '', panel = None, settings = {}):
        ''' Load any non-passed settings from the GUI '''
        gui_settings = panel.get_settings_from_gui()
        if gui_settings is None:
            return
        for s in gui_settings:
            if s in settings:
                if settings[s] is None:
                    settings[s] = gui_settings[s]
            else:
                settings[s] = gui_settings[s]

        control = settings['control']
        cost = getattr(control, settings['cost_name'])
        algo_params = settings['algo_params']
        cost_params = settings['cost_params']
        settings['cost'] = cost
        state = settings['state']

        ''' Create optimizer/sampler '''
        sampler, index = settings['control'].attach_sampler(state, cost)
        sampler.initialize(state, cost, algo_params, cost_params)
        control.samplers[index]['status'] = process

        if hasattr(panel, 'algorithm_box'):
            algorithm_name = panel.algorithm_box.currentText()
            algo = self.get_algorithm(algorithm_name, panel)
            algo.set_params(algo_params)
            algo.sampler = sampler
            sampler.algorithm = algo
            algo.parent = control
            settings['algorithm'] = algo.run
        else:
            algorithm_name = 'Run'

        ''' Create HistoryPanel task '''
        t = datetime.datetime.strftime(datetime.datetime.now(), '%H:%M')
        row = self.parent.historyPanel.add_event(t, cost.__name__, algorithm_name, process, sampler)

        ''' Run process '''
        if state == {} and process != 'run':
            log.warn('Please select at least one Input node for optimization.')
            return

        stoppable = False
        if process == 'run':
            stoppable = True
        panel._run_thread(panel.run_process, args = (sampler, settings, index, t), stoppable=stoppable)
