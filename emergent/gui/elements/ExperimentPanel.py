from PyQt5.QtWidgets import (QComboBox, QLabel, QTextEdit, QPushButton, QVBoxLayout,
        QWidget, QProgressBar, qApp, QHBoxLayout, QCheckBox, QTabWidget, QLineEdit, QSlider)
from PyQt5.QtCore import *
from emergent.archetypes.optimizer import Optimizer
from emergent.gui.elements.OptimizeTab import OptimizeTab
from emergent.archetypes.parallel import ProcessHandler
from emergent.gui.elements.ServoPanel import ServoLayout
from emergent.gui.elements.RunPanel import RunLayout

from emergent.utility import list_algorithms, list_triggers, list_servos
import inspect
import json
import logging as log
import time
from scipy.stats import linregress
import numpy as np
import datetime
import __main__
import os

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

    def double_parse(self, algo, experiment, algo_edit, experiment_edit):
        ''' Updates the QLineEdits for algorithm and experiment parameters
            with the default dicts parsed from file. For any duplicate keys,
            overwrite from experiment to algorithm. For example, to always use
            20 steps in a grid search, just include "steps":20 in the params
            dict for the @experiment. '''
        exp_params = self.file_to_dict(experiment, experiment, 'experiment')
        algo_params = self.file_to_dict(algo, experiment, 'algorithm')
        for p in algo_params:
            if p in exp_params:
                algo_params[p] = exp_params[p]
                del exp_params[p]
        self.dict_to_edit(exp_params, experiment_edit)
        self.dict_to_edit(algo_params, algo_edit)

    def dict_to_edit(self, d, edit):
        string = json.dumps(d).replace('{', '').replace(',', '\n').replace('}', '')
        edit.setText(string)

    def file_to_dict(self, algo, experiment, param_type):
        ''' Generates parameter suggestions for either the algorithm or experiment
            params, based on the choice of param_type. First attempts to pull relevant
            parameters from a json file in the network's params directory; if this fails,
            then it reads default values from the code. '''
        network_name = __main__.network_path.split('.')[2]
        control = self.parent.treeWidget.currentItem().root

        if not os.path.exists('./networks/%s/params/'%network_name):
            os.mkdir('./networks/%s/params/'%network_name)
        params_filename = './networks/%s/params/'%network_name + '%s.%s.txt'%(control.name, experiment.__name__)
        try:
            ''' Load params from file '''
            with open(params_filename, 'r') as file:
                params = json.load(file)
        except OSError:
            ''' If file does not exist, then load from introspection '''
            params = {'experiment': {}, 'algorithm': {}}
            if param_type == 'algorithm':
                params['algorithm'][algo.__name__] = {}

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
                args = inspect.signature(algo).parameters
                args = list(args.items())
                for a in args:
                    if a[0] != 'params':
                        continue
                    d = str(a[1]).split('=')[1]
                    d = json.loads(d.replace("'", '"'))
                params['algorithm'][algo.__name__] = d

            with open(params_filename, 'w') as file:
                json.dump(params, file)

        ''' Make sure the current algorithm's parameters are contained '''
        if param_type == 'algorithm':
            if algo.__name__ in params['algorithm']:
                return params['algorithm'][algo.__name__]
            else:
                args = inspect.signature(algo).parameters
                args = list(args.items())
                for a in args:
                    if a[0] != 'params':
                        continue
                    d = str(a[1]).split('=')[1]
                    d = json.loads(d.replace("'", '"'))
                with open(params_filename, 'r') as file:
                    params = json.load(file)
                params['algorithm'][algo.__name__] = d
                with open(params_filename, 'w') as file:
                    json.dump(params, file)
                return d
        else:
            return params['experiment']
    #
    # def save_experiment_params(self, panel):
    #     network_name = __main__.network_path.split('.')[2]
    #     control = self.parent.treeWidget.currentItem().root
    #     experiment = getattr(control, panel.cost_box.currentText())
    #     params_filename = './networks/%s/params/'%network_name + '%s.%s.txt'%(control.name, experiment.__name__)
    #
    #     ''' Pull params from gui '''
    #     edit = panel.cost_params_edit
    #     cost_params = edit.toPlainText().replace('\n',',').replace("'", '"')
    #     cost_params = json.loads('{' + cost_params + '}')
    #     ''' Load old params from file '''
    #     with open(params_filename, 'r') as file:
    #         old_cost_params = json.load(file)
    #
    #     ''' Update old params with new values and save to file '''
    #     for p in cost_params:
    #         old_cost_params['experiment'][p] = cost_params[p]
    #     with open(params_filename, 'w') as file:
    #         json.dump(old_cost_params, file)

    def save_params(self, panel, param_type):
        ''' param_type: 'experiment' or 'algorithm' '''
        network_name = __main__.network_path.split('.')[2]
        control = self.parent.treeWidget.currentItem().root
        algorithm = getattr(Optimizer, panel.algorithm_box.currentText().replace(' ', '_'))
        experiment = getattr(control, panel.cost_box.currentText())
        params_filename = './networks/%s/params/'%network_name + '%s.%s.txt'%(control.name, experiment.__name__)

        ''' Pull params from gui '''
        edit_name = {'experiment': 'cost', 'algorithm': 'algorithm'}[param_type]
        edit = getattr(panel, edit_name + '_params_edit')
        params = edit.toPlainText().replace('\n',',').replace("'", '"')
        params = json.loads('{' + params + '}')

        if panel.name == 'Optimize':
            f = {'algorithm': panel.get_params, 'experiment': panel.get_cost_params}[param_type]
            params = f()

        ''' Load old params from file '''
        with open(params_filename, 'r') as file:
            old_params = json.load(file)

        ''' Update old params with new values and save to file '''
        for p in params:
            if param_type == 'experiment':
                old_params[param_type][p] = params[p]
            else:
                old_params[param_type][algorithm.__name__][p] = params[p]
        with open(params_filename, 'w') as file:
            json.dump(old_params, file)

    def update_control_panel(self, panel, exp_or_error, algo):
        ''' Updates the algorithm box with the methods available to the currently selected control. '''
        control = self.parent.treeWidget.currentItem().root
        if algo:
            panel.algorithm_box.clear()
            if exp_or_error == 'experiment':
                for item in list_algorithms():
                    panel.algorithm_box.addItem(item.replace('_',' '))
            elif exp_or_error == 'error':
                for item in list_servos():
                    panel.algorithm_box.addItem(item.replace('_',' '))
        if exp_or_error == 'error':
            panel.cost_box.clear()
            for item in control.list_errors():
                panel.cost_box.addItem(item)
        elif exp_or_error == 'experiment':
            panel.cost_box.clear()
            for item in control.list_costs():
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
        # control = self.parent.treeWidget.get_selected_control()
        control = self.parent.treeWidget.currentItem().root
        experiment = getattr(control, panel.cost_box.currentText())
        d = self.file_to_dict(experiment, experiment, 'experiment')
        self.dict_to_edit(d, panel.cost_params_edit)

    def update_algorithm_and_experiment(self, panel):
        if panel.cost_box.currentText() is '':
            return
        # try:
        algo = getattr(Optimizer, panel.algorithm_box.currentText().replace(' ','_'))
        # control = self.parent.treeWidget.get_selected_control()
        control = self.parent.treeWidget.currentItem().root
        experiment = getattr(control, panel.cost_box.currentText())
        exp_params = self.file_to_dict(experiment, experiment, 'experiment')
        algo_params = self.file_to_dict(algo, experiment, 'algorithm')
        self.dict_to_edit(exp_params, panel.cost_params_edit)
        self.dict_to_edit(algo_params, panel.algorithm_params_edit)

        # except AttributeError:
        #     print('attribute error!')
        #     return

        if panel.name == 'Optimize':
            panel.clear_parameters()
            for p in algo_params:
                panel.add_parameter(p, str(algo_params[p]))
            panel.clear_cost_parameters()
            for p in exp_params:
                panel.add_cost_parameter(p, str(exp_params[p]))




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
        optimizer, index = settings['control'].attach_optimizer(state, cost)
        sampler, index = settings['control'].attach_sampler(state, cost, optimizer=optimizer)
        sampler.initialize(state, cost, algo_params, cost_params)
        control.optimizers[index]['status'] = process
        control.samplers[index]['status'] = process

        if hasattr(panel, 'algorithm_box'):
            algorithm_name = panel.algorithm_box.currentText().replace(' ', '_')
            algo = getattr(optimizer, algorithm_name)
            settings['algorithm'] = algo
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
