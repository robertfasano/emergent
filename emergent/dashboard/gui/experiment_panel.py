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
from emergent.dashboard.gui import RunLayout

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
        run_tab = QWidget()
        self.run_panel = RunLayout(self)
        run_tab.setLayout(self.run_panel)
        run_tab.setStyleSheet('background-color: rgba(255, 255, 255, 50%)')
        self.tab_widget.addTab(run_tab, 'Run')


        self.update_panel()

        self.tab_widget.currentChanged.connect(self.update_panel)

    def update_panel(self):
        self.panel = self.tab_widget.currentWidget().layout()


    def update_hub_panel(self, panel, exp_or_error, algo):
        ''' Updates the algorithm box with the methods available to the currently selected hub. '''
        hub = self.dashboard.tree_widget.currentItem().parent().parent().text(0)


        panel.experiment_box.clear()
        for item in self.dashboard.p2p.get('experiments', params={'hub': hub}):
            panel.experiment_box.addItem(item)



    def update_hub(self):
        hub = self.dashboard.tree_widget.currentItem().parent().parent().text(0)
        if hub == self.current_hub:
            return
        else:
            self.current_hub = hub

        self.update_hub_panel(self.run_panel, 'experiment', False)
        self.update_experiment(self.run_panel)


    def update_experiment(self, panel):
        ''' Read default params dict from source code and insert it in self.cost_params_edit. '''
        if panel.experiment_box.currentText() == '':
            return
        hub = self.dashboard.tree_widget.currentItem().parent().parent().text(0)
        # d = recommender.load_experiment_parameters(hub, panel.experiment_box.currentText())
        d = self.dashboard.p2p.get('experiment_params', params={'hub': hub, 'experiment': panel.experiment_box.currentText()})
        panel.experiment_table.set_parameters(d)

        ''' update triggers '''
        panel.trigger_box.clear()
        panel.trigger_box.addItem('')
        for t in self.dashboard.p2p.get('triggers', params={'hub': hub}):
            panel.trigger_box.addItem(t)

    def start_process(self, process='', threaded=True):
        ''' Load settings from the GUI and start a process. '''
        panel = getattr(self, process+'_panel')
        settings = panel.get_settings_from_gui()
        message = {'op': 'run', 'params': settings}
        self.dashboard.p2p.send(message)
