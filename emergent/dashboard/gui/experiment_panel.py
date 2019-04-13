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
from emergent.modules import Sampler
from emergent.dashboard.gui import MeasureLayout, ModelLayout, ServoLayout, PipelineLayout

class ExperimentLayout(QVBoxLayout):
    def __init__(self, dashboard):
        QVBoxLayout.__init__(self)
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

        ''' Create Pipeline tab '''
        pipeline_tab = QWidget()
        self.pipeline_panel = PipelineLayout(self)
        pipeline_tab.setLayout(self.pipeline_panel)
        pipeline_tab.setStyleSheet('background-color: rgba(255, 255, 255, 50%)')
        self.tab_widget.addTab(pipeline_tab, 'Pipeline')

        self.update_panel()

        self.tab_widget.currentChanged.connect(self.update_panel)

    def update_panel(self):
        self.panel = self.tab_widget.currentWidget().layout()


    def update_choices(self, panel):
        ''' Updates the algorithm box with the methods available to the currently selected hub. '''
        hub = self.dashboard.tree_widget.currentItem().parent().parent().text(0)

        if hasattr(panel, 'experiment_box'):
            panel.experiment_box.clear()
            for item in self.dashboard.get('hubs/%s/experiments'%hub):
                panel.experiment_box.addItem(item)

        if hasattr(panel, 'error_box'):
            panel.error_box.clear()
            for item in self.dashboard.get('hubs/%s/errors'%hub):
                panel.error_box.addItem(item)

        for x in ['model', 'sampler', 'servo']:
            if hasattr(panel, '%s_box'%x):
                getattr(panel, '%s_box'%x).clear()
                if x == 'model':
                    panel.model_box.addItem('None')
                for item in self.dashboard.get('%ss'%x):
                    getattr(panel, '%s_box'%x).addItem(item)

        if hasattr(panel, 'trigger_box'):
            ''' update triggers '''
            panel.trigger_box.clear()
            panel.trigger_box.addItem('')
            for t in self.dashboard.get('hubs/%s/triggers'%hub):
                panel.trigger_box.addItem(t)


    def update_hub(self):
        hub = self.dashboard.tree_widget.get_selected_hub()
        if hub == self.current_hub or hub is None:
            return
        else:
            self.current_hub = hub

        self.update_choices(self.measure_panel)
        self.measure_panel.update_params()
        self.update_choices(self.model_panel)
        self.model_panel.update_params()

        self.update_choices(self.servo_panel)
        self.servo_panel.update_params()

        self.update_choices(self.pipeline_panel)

    def start_process(self, process='', threaded=True):
        ''' Load settings from the GUI and start a process. '''
        panel = getattr(self, process+'_panel')
        settings = panel.get_settings_from_gui()
        self.dashboard.post('run', settings)
