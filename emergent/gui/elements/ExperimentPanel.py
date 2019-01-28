''' The Experiment panel contains several tabs for launching single/multi-shot or
    continuous measurements and running optimizations or servos. Most of the methods
    defined here are for loading GUI displays based on user selections:

    * Selecting a Hub or any of its children will cause the hub's @experiment methods to be listed in a combo box.
    * Choosing an experiment will load the default parameters from file.
    * Default experiment parameters can be overwritten from the current parameters or from the @experiment's default params.
    * Choosing an algorithm will load the default parameters from file.
    * Default algorithm parameters can be overwritten from the current parameters or from the Algorithm's default Parameters.

'''
from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QTabWidget)
from PyQt5.QtCore import *
from emergent.gui.elements import OptimizeLayout, ServoLayout, RunLayout
from emergent.modules import Sampler, recommender, ProcessHandler
import json
import logging as log
import datetime
#import __main__
from emergent.utility import list_errors, list_experiments, list_triggers


class ExperimentLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent
        self.tabWidget = QTabWidget()
        self.addWidget(self.tabWidget)
        self.current_hub = None
        self.parent.treeWidget.itemSelectionChanged.connect(self.update_hub)

        ''' Create Optimizer tab '''
        self.optimizeTab = QWidget()
        self.optimizePanel = OptimizeLayout(self)
        self.optimizeTab.setLayout(self.optimizePanel)
        self.optimizeTab.setStyleSheet('background-color: rgba(255, 255, 255, 50%)')
        # self.tabWidget.addTab(self.optimizeTab, 'Optimize')

        ''' Create Servo tab '''
        self.servoTab = QWidget()
        self.servoPanel = ServoLayout(self)
        self.servoTab.setLayout(self.servoPanel)
        self.servoTab.setStyleSheet('background-color: rgba(255, 255, 255, 50%)')
        # self.tabWidget.addTab(self.servoTab, 'Servo')

        ''' Create Run tab '''
        runTab = QWidget()
        self.runPanel = RunLayout(self)
        runTab.setLayout(self.runPanel)
        runTab.setStyleSheet('background-color: rgba(255, 255, 255, 50%)')
        self.tabWidget.addTab(runTab, 'Run')

        self.update_panel()

        self.tabWidget.currentChanged.connect(self.update_panel)

    def update_panel(self):
        self.panel = self.tabWidget.currentWidget().layout()

    def get_default_params(self, name, panel):
        return {'Optimize': recommender.get_default_algorithm_params,
                'Servo': recommender.get_default_servo_params}[panel.name](name)

    def get_algorithm(self, name, panel):
        return {'Optimize': recommender.get_algorithm,
                'Servo': recommender.get_servo}[panel.name](name)

    def get_description(self, panel, algo_name, parameter):
        params = self.get_algorithm(algo_name, panel).params
        return params[parameter].description

    def list_algorithms(self, panel):
        return {'Optimize': recommender.list_algorithms,
                'Servo': recommender.list_servos}[panel.name]()

    def save_default_algorithm(self):
        if self.panel.name == 'Run':
            return
        hub = self.parent.treeWidget.currentItem().root
        experiment_name = self.panel.experiment_box.currentText()
        algorithm_name = self.panel.algorithm_box.currentText()
        recommender.save_default_algorithm(hub, experiment_name, algorithm_name)

    def save_params(self, panel, param_type):
        ''' param_type: 'experiment' or 'algorithm' '''
        network_name = self.parent.network.name
        hub = self.parent.treeWidget.currentItem().root

        experiment = getattr(hub, panel.experiment_box.currentText())
        params_filename = './networks/%s/params/'%network_name + '%s.%s.txt'%(hub.name, experiment.__name__)

        ''' Pull params from gui '''
        if param_type == 'algorithm':
            params = panel.algorithm_table.get_params()
        else:
            params = panel.experiment_table.get_params()
        ''' Load old params from file '''
        with open(params_filename, 'r') as file:
            old_params = json.load(file)

        ''' Update old params with new values and save to file '''
        for p in params:
            if param_type == 'experiment':
                old_params[param_type][p] = params[p]
            else:
                algorithm_name = panel.algorithm_box.currentText()
                old_params[param_type][algorithm_name][p] = params[p]
        with open(params_filename, 'w') as file:
            json.dump(old_params, file)

    def update_hub_panel(self, panel, exp_or_error, algo):
        ''' Updates the algorithm box with the methods available to the currently selected hub. '''
        hub = self.parent.treeWidget.currentItem().root
        if algo:
            panel.algorithm_box.clear()
            if exp_or_error == 'experiment':
                for item in self.list_algorithms(panel):
                    panel.algorithm_box.addItem(item.replace('_',' '))
            elif exp_or_error == 'error':
                for item in self.list_algorithms(panel):
                    panel.algorithm_box.addItem(item.replace('_',' '))
        if exp_or_error == 'error':
            panel.experiment_box.clear()
            for item in list_errors(hub):
                panel.experiment_box.addItem(item)
        elif exp_or_error == 'experiment':
            panel.experiment_box.clear()
            for item in list_experiments(hub):
                panel.experiment_box.addItem(item)

        ''' Show/hide servo tab based on whether the hub has any error methods'''
        index = self.tabWidget.indexOf(self.servoTab)
        if list_errors(hub) == []:
            self.tabWidget.removeTab(self.tabWidget.indexOf(self.servoTab))
        else:
            if index == -1:
                self.tabWidget.addTab(self.servoTab, 'Servo')

        ''' Show/hide optimize tab if we do/don't have inputs selected '''
        index = self.tabWidget.indexOf(self.optimizeTab)
        state = self.parent.treeWidget.get_selected_state()
        if len(state) == 0:
            self.tabWidget.removeTab(self.tabWidget.indexOf(self.optimizeTab))
        else:
            if index == -1:
                self.tabWidget.addTab(self.optimizeTab, 'Optimize')




    def update_hub(self):
        hub = self.parent.treeWidget.currentItem().root
        if hub == self.current_hub:
            return
        else:
            self.current_hub = hub
        self.update_hub_panel(self.optimizePanel, 'experiment', True)
        self.update_algorithm_and_experiment(self.optimizePanel)
        self.update_hub_panel(self.runPanel, 'experiment', False)
        self.update_experiment(self.runPanel)
        self.update_hub_panel(self.servoPanel, 'error', True)
        self.update_algorithm_and_experiment(self.servoPanel)

    def update_experiment(self, panel):
        ''' Read default params dict from source code and insert it in self.cost_params_edit. '''
        if panel.experiment_box.currentText() is '':
            return
        hub = self.parent.treeWidget.currentItem().root
        experiment = getattr(hub, panel.experiment_box.currentText())
        d = recommender.load_experiment_parameters(hub, experiment.__name__)
        panel.experiment_table.set_parameters(d)

        ''' update triggers '''
        panel.trigger_box.clear()
        panel.trigger_box.addItem('')
        for t in list_triggers(hub):
            panel.trigger_box.addItem(t)

    def update_algorithm_and_experiment(self, panel, default = False, update_algorithm = True, update_experiment = True):
        if panel.experiment_box.currentText() is '':
            return
        if hasattr(panel, 'algorithm_box'):
            if panel.algorithm_box.currentText() is '':
                return
        hub = self.parent.treeWidget.currentItem().root
        experiment_name = panel.experiment_box.currentText()
        if experiment_name == '':
            return
        if update_algorithm:
            algo_name = panel.algorithm_box.currentText()
            if panel.name == 'Optimize':
                algo_params = recommender.load_algorithm_parameters(hub, experiment_name, algo_name, default = default)
            elif panel.name == 'Servo':
                algo_params = recommender.load_servo_parameters(hub, experiment_name, algo_name, default = default)
            panel.algorithm_table.set_parameters(algo_params)
        if update_experiment:
            exp_params = recommender.load_experiment_parameters(hub, experiment_name)

            panel.experiment_table.set_parameters(exp_params)
            if panel.name == 'Optimize':
                default_name = recommender.get_default_algorithm(hub, experiment_name).name
                panel.algorithm_box.setCurrentText(default_name)

    def fill_settings_from_gui(self, panel, settings):
        gui_settings = panel.get_settings_from_gui()
        if gui_settings is None:
            return
        for s in gui_settings:
            if s in settings:
                if settings[s] is None:
                    settings[s] = gui_settings[s]
            else:
                settings[s] = gui_settings[s]
        return settings

    def start_process(self, process = '', settings = {}, threaded = True, load_from_gui = False):
        ''' Load any non-passed settings from the GUI '''
        ''' Settings contains the following fields:
            experiment_name: str
            cost_params: dict
            algo_params: dict
            hub: node
            state: dict

        '''
        panel = getattr(self, process+'Panel')

        ''' Pull settings from the gui and fill in any missing options '''
        if load_from_gui:
            settings = self.fill_settings_from_gui(panel, settings)
            # if settings is None:
            #     return
        settings['experiment'] = getattr(settings['hub'], settings['experiment_name'])
        if hasattr(panel, 'algorithm_box'):
            algorithm_name = panel.algorithm_box.currentText()
            settings['algorithm'] = self.get_algorithm(algorithm_name, panel)
            settings['algorithm'].set_params(settings['algorithm_params'])
            name = algorithm_name
        else:
            settings['algorithm'] = None
            settings['algorithm_params'] = None
            name = 'Run'
        t = datetime.datetime.now().strftime('%Y%m%dT%H%M')
        sampler = Sampler(name,
                          settings['state'],
                          settings['hub'],
                          settings['experiment'],
                          settings['experiment_params'],
                          settings['algorithm'],
                          settings['algorithm_params'],
                          t=t)

        ''' Create taskPanel task '''
        row = self.parent.taskPanel.add_event(sampler)

        ''' Assign trigger '''
        if process == 'run':
            sampler.trigger = None
            if panel.trigger_box.currentText() != '':
                sampler.trigger = getattr(sampler.hub, panel.trigger_box.currentText())

        ''' Run process '''
        if settings['state'] == {} and process != 'run':
            log.warn('Please select at least one Input node for optimization.')
            return
        stoppable = False
        if process == 'run':
            stoppable = True
        if threaded:
            panel._run_thread(panel.run_process, args = (sampler,), stoppable=stoppable)
        else:
            panel.run_process(sampler)
