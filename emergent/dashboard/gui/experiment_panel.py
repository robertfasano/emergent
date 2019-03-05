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
from emergent.dashboard.gui import MeasureLayout, ModelLayout, ServoLayout

class ExperimentLayout(QVBoxLayout, ProcessHandler):
    def __init__(self, dashboard):
        QVBoxLayout.__init__(self)
        ProcessHandler.__init__(self)
        self.dashboard = dashboard
        self.tab_widget = QTabWidget()
        self.addWidget(self.tab_widget)
        self.current_hub = None
        self.dashboard.tree_widget.itemSelectionChanged.connect(self.update_hub)


        ''' Create Run tab '''
        measure_tab = QWidget()
        self.measure_panel = MeasureLayout(self)
        measure_tab.setLayout(self.measure_panel)
        measure_tab.setStyleSheet('background-color: rgba(255, 255, 255, 50%)')
        self.tab_widget.addTab(measure_tab, 'Measure')

        ''' Create Model tab '''
        model_tab = QWidget()
        self.model_panel = ModelLayout(self)
        model_tab.setLayout(self.model_panel)
        model_tab.setStyleSheet('background-color: rgba(255, 255, 255, 50%)')
        self.tab_widget.addTab(model_tab, 'Model')

        ''' Create Servo tab '''
        servo_tab = QWidget()
        self.servo_panel = ServoLayout(self)
        servo_tab.setLayout(self.servo_panel)
        servo_tab.setStyleSheet('background-color: rgba(255, 255, 255, 50%)')
        self.tab_widget.addTab(servo_tab, 'Servo')

        self.update_panel()

        self.tab_widget.currentChanged.connect(self.update_panel)

    def update_panel(self):
        self.panel = self.tab_widget.currentWidget().layout()


    def update_hub_panel(self, panel):
        ''' Updates the algorithm box with the methods available to the currently selected hub. '''
        hub = self.dashboard.tree_widget.currentItem().parent().parent().text(0)

        if hasattr(panel, 'experiment_box'):
            panel.experiment_box.clear()
            for item in self.dashboard.p2p.get('experiments', params={'hub': hub}):
                panel.experiment_box.addItem(item)

        if hasattr(panel, 'error_box'):
            panel.error_box.clear()
            for item in self.dashboard.p2p.get('errors', params={'hub': hub}):
                panel.error_box.addItem(item)

        for x in ['model', 'sampler', 'algorithm', 'servo']:
            if hasattr(panel, '%s_box'%x):
                getattr(panel, '%s_box'%x).clear()
                for item in self.dashboard.p2p.get('%ss'%x):
                    getattr(panel, '%s_box'%x).addItem(item)


    def update_hub(self):
        hub = self.dashboard.tree_widget.currentItem().parent().parent().text(0)
        if hub == self.current_hub:
            return
        else:
            self.current_hub = hub

        self.update_hub_panel(self.measure_panel)
        self.update_experiment(self.measure_panel)

        self.update_hub_panel(self.model_panel)
        self.update_experiment(self.model_panel)
        self.update_model(self.model_panel)
        self.update_sampler(self.model_panel)

        self.update_hub_panel(self.servo_panel)
        self.update_error(self.servo_panel)
        self.update_servo(self.servo_panel)

    def update_experiment(self, panel):
        if panel.experiment_box.currentText() == '':
            return
        hub = self.dashboard.tree_widget.get_selected_hub()
        d = self.dashboard.p2p.get('experiment_params', params={'hub': hub, 'experiment': panel.experiment_box.currentText()})
        panel.experiment_table.set_parameters(d)

        if hasattr(panel, 'trigger_box'):
            ''' update triggers '''
            panel.trigger_box.clear()
            panel.trigger_box.addItem('')
            for t in self.dashboard.p2p.get('triggers', params={'hub': hub}):
                panel.trigger_box.addItem(t)

    def update_error(self, panel):
        if panel.error_box.currentText() == '':
            return
        hub = self.dashboard.tree_widget.get_selected_hub()
        d = self.dashboard.p2p.get('error_params', params={'hub': hub, 'error': panel.error_box.currentText()})
        panel.error_table.set_parameters(d)

        if hasattr(panel, 'trigger_box'):
            ''' update triggers '''
            panel.trigger_box.clear()
            panel.trigger_box.addItem('')
            for t in self.dashboard.p2p.get('triggers', params={'hub': hub}):
                panel.trigger_box.addItem(t)

    def update_model(self, panel):
        if panel.model_box.currentText() == '':
            return
        hub = self.dashboard.tree_widget.get_selected_hub()
        d = self.dashboard.p2p.get('model_params', params={'hub': hub, 'model': panel.model_box.currentText()})
        panel.model_table.set_parameters(d)

    def update_sampler(self, panel):
        if panel.sampler_box.currentText() == '':
            return
        hub = self.dashboard.tree_widget.get_selected_hub()
        d = self.dashboard.p2p.get('sampler_params', params={'hub': hub, 'sampler': panel.sampler_box.currentText()})
        panel.sampler_table.set_parameters(d)

    def update_servo(self, panel):
        if panel.servo_box.currentText() == '':
            return
        hub = self.dashboard.tree_widget.get_selected_hub()
        d = self.dashboard.p2p.get('servo_params', params={'hub': hub, 'servo': panel.servo_box.currentText()})
        panel.servo_table.set_parameters(d)

    def start_process(self, process='', threaded=True):
        ''' Load settings from the GUI and start a process. '''
        panel = getattr(self, process+'_panel')
        settings = panel.get_settings_from_gui()
        message = {'op': 'run', 'params': settings}
        self.dashboard.p2p.send(message)