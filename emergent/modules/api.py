from emergent.utilities.introspection import list_experiments, list_triggers
from emergent.utilities import recommender
from emergent.modules.parallel import ProcessHandler
from emergent.modules import Sampler

class DashAPI():
    def __init__(self, dashboard):
        self.dashboard = dashboard

    def get(self, target):
        if target == 'state':
            return self.dashboard.tree_widget.get_state()

    def set(self, target, value):
        if target == 'state':
            self.dashboard.tree_widget.set_state(value)


class MainAPI():
    def __init__(self, network):
        self.network = network
        self.manager = ProcessHandler()

    def get(self, target, params = {}):
        if target == 'state':
            return self.network.state()

        if target == 'settings':
            return self.network.settings()

        elif target == 'experiments':
            hub = self.network.hubs[params['hub']]
            return list_experiments(hub)

        elif target == 'triggers':
            hub = self.network.hubs[params['hub']]
            return list_triggers(hub)

        elif target == 'experiment_params':
            hub = self.network.hubs[params['hub']]
            params = recommender.load_experiment_parameters(hub, params['experiment'])
            return params

    def run(self, settings):
        settings['hub'] = self.network.hubs[settings['hub']]
        settings['experiment']['instance'] = getattr(settings['hub'], settings['experiment']['name'])
        sampler = Sampler('sampler', settings)

        # ''' Create task_panel task '''
        # self.dashboard.task_panel.add_event(sampler)


        if 'trigger' in settings['process']:
            trigger = getattr(settings['hub'], settings['process']['trigger'])

        ''' Run process '''
        if settings['state'] == {} and settings['process']['type'] != 'run':
            log.warning('Please select at least one Input node.')
            return

        func = sampler._solve
        if settings['process']['type'] == 'run':
            func = sampler._run

        self.manager._run_thread(func, stoppable=False)


    def set(self, target, value):
        if target == 'state':
            self.network.actuate(value, send_over_p2p = False)

        elif target == 'settings':
            self.network.set_settings(value)
