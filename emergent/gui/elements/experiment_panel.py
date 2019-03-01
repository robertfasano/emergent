''' The Experiment panel contains several tabs for launching single/multi-shot or
    continuous measurements and running optimizations or servos. Most of the methods
    defined here are for loading GUI displays based on user selections:

    * Selecting a Hub or any of its children will cause the hub's @experiment
      methods to be listed in a combo box.
    * Choosing an experiment will load the default parameters from file.
    * Default experiment parameters can be overwritten from the current parameters
      or from the @experiment's default params.
    * Choosing an algorithm will load the default parameters from file.
    * Default algorithm parameters can be overwritten from the current parameters
      or from the Algorithm's default Parameters.

'''
import json
import logging as log
from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QTabWidget)
from emergent.utilities.introspection import list_errors, list_experiments, list_triggers
from emergent.utilities import recommender
from emergent.modules import Sampler, ProcessHandler
from emergent.gui.elements import OptimizeLayout, ServoLayout, RunLayout, MonitorLayout, ModelLayout

class ExperimentLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, parent):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.parent = parent
        self.tab_widget = QTabWidget()
        self.addWidget(self.tab_widget)
        self.current_hub = None
        self.parent.tree_widget.itemSelectionChanged.connect(self.update_hub)

        ''' Create Optimizer tab '''
        self.optimize_tab = QWidget()
        self.optimize_panel = OptimizeLayout(self)
        self.optimize_tab.setLayout(self.optimize_panel)
        self.optimize_tab.setStyleSheet('background-color: rgba(255, 255, 255, 50%)')
        # self.tab_widget.addTab(self.optimize_tab, 'Optimize')

        ''' Create Servo tab '''
        self.servo_tab = QWidget()
        self.servo_panel = ServoLayout(self)
        self.servo_tab.setLayout(self.servo_panel)
        self.servo_tab.setStyleSheet('background-color: rgba(255, 255, 255, 50%)')
        # self.tab_widget.addTab(self.servo_tab, 'Servo')

        ''' Create Run tab '''
        run_tab = QWidget()
        self.run_panel = RunLayout(self)
        run_tab.setLayout(self.run_panel)
        run_tab.setStyleSheet('background-color: rgba(255, 255, 255, 50%)')
        self.tab_widget.addTab(run_tab, 'Run')


        ''' Create Monitor tab '''
        monitor_tab = QWidget()
        self.monitor_panel = MonitorLayout(self.parent.network, self.parent)
        monitor_tab.setLayout(self.monitor_panel)
        monitor_tab.setStyleSheet('background-color: rgba(255, 255, 255, 50%)')
        self.tab_widget.addTab(monitor_tab, 'Monitor')

        ''' Create Model tab '''
        self.model_tab = QWidget()
        self.model_panel = ModelLayout(self)
        self.model_tab.setLayout(self.model_panel)
        self.model_tab.setStyleSheet('background-color: rgba(255, 255, 255, 50%)')
        self.tab_widget.addTab(self.model_tab, 'Model')

        self.update_panel()

        self.tab_widget.currentChanged.connect(self.update_panel)

    def update_panel(self):
        self.panel = self.tab_widget.currentWidget().layout()

    def get_default_params(self, name, panel):
        if panel.name == 'Optimize':
            return recommender.get_default_params('algorithm', name)
        elif panel.name == 'Servo':
            return recommender.get_default_params('servo', name)

    def list_algorithms(self, panel):
        if panel.name == 'Optimize':
            return recommender.list_classes('algorithm')
        elif panel.name == 'Servo':
            return recommender.list_classes('servo')
        elif panel.name == 'Model':
            return recommender.list_classes('sampler')

    def list_models(self):
        return recommender.list_classes('model')

    def save_default_algorithm(self):
        if self.panel.name == 'Run':
            return
        hub = self.parent.tree_widget.currentItem().root
        experiment_name = self.panel.experiment_box.currentText()
        algorithm_name = self.panel.algorithm_box.currentText()
        recommender.save_default_algorithm(hub, experiment_name, algorithm_name)

    def save_params(self, panel, param_type):
        ''' param_type: 'experiment' or 'algorithm' '''
        network_name = self.parent.network.name
        hub = self.parent.tree_widget.currentItem().root

        experiment = getattr(hub, panel.experiment_box.currentText())
        params_filename = './networks/%s/params/'%network_name
        params_filename += '%s.%s.txt'%(hub.name, experiment.__name__)

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
        hub = self.parent.tree_widget.currentItem().root
        if algo:
            panel.algorithm_box.clear()
            if exp_or_error == 'experiment':
                for item in self.list_algorithms(panel):
                    panel.algorithm_box.addItem(item.replace('_', ' '))
            elif exp_or_error == 'error':
                for item in self.list_algorithms(panel):
                    panel.algorithm_box.addItem(item.replace('_', ' '))
        if exp_or_error == 'error':
            panel.experiment_box.clear()
            for item in list_errors(hub):
                panel.experiment_box.addItem(item)
        elif exp_or_error == 'experiment':
            panel.experiment_box.clear()
            for item in list_experiments(hub):
                panel.experiment_box.addItem(item)
        if hasattr(panel, 'model_box'):
            panel.model_box.clear()
            for m in self.list_models():
                panel.model_box.addItem(m)
        if hasattr(panel, 'sampler_box'):
            panel.sampler_box.clear()
            for s in recommender.list_classes('sampler'):
                panel.sampler_box.addItem(s)
        ''' Show/hide servo tab based on whether the hub has any error methods'''
        index = self.tab_widget.indexOf(self.servo_tab)
        if list_errors(hub) == []:
            self.tab_widget.removeTab(self.tab_widget.indexOf(self.servo_tab))
        else:
            if index == -1:
                self.tab_widget.addTab(self.servo_tab, 'Servo')

    def update_hub(self):
        hub = self.parent.tree_widget.currentItem().root
        if hub == self.current_hub:
            return
        else:
            self.current_hub = hub
        self.update_hub_panel(self.optimize_panel, 'experiment', True)
        self.update_algorithm_and_experiment(self.optimize_panel)

        self.update_hub_panel(self.run_panel, 'experiment', False)
        self.update_experiment(self.run_panel)

        self.update_hub_panel(self.servo_panel, 'error', True)
        self.update_algorithm_and_experiment(self.servo_panel)

        self.update_hub_panel(self.model_panel, 'experiment', False)
        self.update_algorithm_and_experiment(self.model_panel)


    def update_experiment(self, panel):
        ''' Read default params dict from source code and insert it in self.cost_params_edit. '''
        if panel.experiment_box.currentText() == '':
            return
        hub = self.parent.tree_widget.currentItem().root
        experiment = getattr(hub, panel.experiment_box.currentText())
        d = recommender.load_experiment_parameters(hub, experiment.__name__)
        panel.experiment_table.set_parameters(d)

        ''' update triggers '''
        panel.trigger_box.clear()
        panel.trigger_box.addItem('')
        for t in list_triggers(hub):
            panel.trigger_box.addItem(t)

    def update_algorithm_and_experiment(self, panel, default=False, update_algorithm=True, update_experiment=True):
        if panel.experiment_box.currentText() == '':
            return
        if hasattr(panel, 'algorithm_box'):
            if panel.algorithm_box.currentText() == '':
                return
        if hasattr(panel, 'sampler_box'):
            if panel.sampler_box.currentText() == '':
                return
        hub = self.parent.tree_widget.currentItem().root
        experiment_name = panel.experiment_box.currentText()
        if experiment_name == '':
            return
        if hasattr(panel, 'trigger_box'):
            panel.trigger_box.clear()
            panel.trigger_box.addItem('')
            for t in list_triggers(hub):
                panel.trigger_box.addItem(t)

        if update_algorithm:
            if panel.name == 'Optimize':
                algo_name = panel.algorithm_box.currentText()
                algo_params = recommender.load_algorithm_parameters(hub,
                                                                    experiment_name,
                                                                    algo_name,
                                                                    'algorithm',
                                                                    default=default)
            elif panel.name == 'Servo':
                algo_name = panel.algorithm_box.currentText()
                algo_params = recommender.load_algorithm_parameters(hub,
                                                                experiment_name,
                                                                algo_name,
                                                                'servo',
                                                                default=default)
            elif panel.name == 'Model':
                algo_name = panel.sampler_box.currentText()
                algo_params = recommender.load_algorithm_parameters(hub,
                                                                    experiment_name,
                                                                    algo_name,
                                                                    'sampler',
                                                                    default=default)
            panel.algorithm_table.set_parameters(algo_params)
        if update_experiment:
            exp_params = recommender.load_experiment_parameters(hub, experiment_name)

            panel.experiment_table.set_parameters(exp_params)
            if panel.name == 'Optimize':
                default_name = recommender.get_default_algorithm(hub, experiment_name).name
                panel.algorithm_box.setCurrentText(default_name)

        if hasattr(panel, 'model_table'):
            model_name = panel.model_box.currentText()
            model_params = recommender.get_default_params('model', model_name)
            panel.model_table.set_parameters(model_params)

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

    def start_process(self, process='', threaded=True):
        ''' Load settings from the GUI and start a process. '''
        panel = getattr(self, process+'_panel')
        settings = panel.get_settings_from_gui()
        settings['experiment']['instance'] = getattr(settings['hub'], settings['experiment']['name'])

        if 'algorithm' in settings:
            name = settings['algorithm']['name']
            if 'end at' in settings['process']:
                settings['algorithm']['instance'].end_at = settings['process']['end at']
        else:
            name = 'Run'

        sampler = Sampler(name, settings)

        ''' Create task_panel task '''
        self.parent.task_panel.add_event(sampler)

        ''' Assign trigger '''
        if hasattr(panel, 'trigger_box'):
            sampler.trigger = None
            if panel.trigger_box.currentText() != '':
                sampler.trigger = getattr(sampler.hub, panel.trigger_box.currentText())

        ''' Run process '''
        if settings['state'] == {} and process != 'run':
            log.warning('Please select at least one Input node.')
            return
            
        func = sampler._solve
        if process == 'run':
            func = sampler._run

        if threaded:
            panel._run_thread(func, stoppable=False)
        else:
            func()
