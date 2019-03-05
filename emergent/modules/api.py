from emergent.utilities import recommender, introspection
from emergent.modules.parallel import ProcessHandler
from emergent.modules import Sampler
import datetime
import uuid

class DashAPI():
    def __init__(self, dashboard):
        self.dashboard = dashboard

    def event(self, event = {}):
        ''' Adds an event to the TaskPanel '''
        self.dashboard.task_panel.add_event(event)

    def get(self, target, params = {}):
        if target == 'state':
            return self.dashboard.tree_widget.get_state()

    def set(self, target, value):
        if target == 'state':
            self.dashboard.tree_widget.set_state(value)


class MainAPI():
    def __init__(self, network):
        self.network = network
        self.manager = ProcessHandler()

    def check(self, params):
        ''' Check whether the sampler with the given uuid is active. '''
        hub = self.network.hubs[params['hub']]
        for sampler in hub.samplers.values():
            if sampler.id == params['id']:
                return sampler.active

    def get(self, target, params = {}):
        if target == 'state':
            return self.network.state()

        if target == 'settings':
            return self.network.settings()

        elif target == 'experiments':
            hub = self.network.hubs[params['hub']]
            return introspection.list_experiments(hub)

        elif target == 'errors':
            hub = self.network.hubs[params['hub']]
            return introspection.list_errors(hub)

        elif target == 'triggers':
            hub = self.network.hubs[params['hub']]
            return introspection.list_triggers(hub)

        elif target == 'experiment_params':
            hub = self.network.hubs[params['hub']]
            params = recommender.load_experiment_parameters(hub, params['experiment'])
            return params

        elif target == 'model_params':
            return recommender.get_default_params('model', params['model'])

        elif target == 'sampler_params':
            return recommender.get_default_params('sampler', params['sampler'])

        elif target == 'servo_params':
            return recommender.get_default_params('servo', params['servo'])

        elif target == 'error_params':
            hub = self.network.hubs[params['hub']]
            params = recommender.load_experiment_parameters(hub, params['error'])
            return params

        elif target == 'models':
            return recommender.list_classes('model')

        elif target == 'samplers':
            return recommender.list_classes('sampler')

        elif target == 'servos':
            return recommender.list_classes('servo')

    def run(self, settings):
        settings['hub'] = self.network.hubs[settings['hub']]
        settings['experiment']['instance'] = getattr(settings['hub'], settings['experiment']['name'])

        for x in ['model', 'sampler', 'servo']:
            if x in settings:
                settings[x]['instance'] = recommender.get_class(x, settings[x]['name'])
        sampler = Sampler('sampler', settings)
        sampler.id = str(uuid.uuid1())
        ''' Create task_panel task '''

        params = {'start time': datetime.datetime.now().isoformat(),
                  'experiment': settings['experiment']['name'],
                  'id': sampler.id,
                  'hub': sampler.hub.name}

        if 'algorithm' in settings:
            params['algorithm'] = settings['algorithm']['name']
        message = {'op': 'event', 'params': params}
        self.network.p2p.send(message)


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
