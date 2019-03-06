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

    def shutdown(self):
        print('Shutting down Dashboard.')
        self.dashboard.app.quit()



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
        if 'hub' in params:
            hub = self.network.hubs[params['hub']]
        targets = {'state': self.network.state,
                   'settings': self.network.settings,
                   'experiments': lambda: introspection.list_experiments(hub),
                   'errors': lambda: introspection.list_errors(hub),
                   'triggers': lambda: introspection.list_triggers(hub),
                   'experiment_params': lambda: recommender.load_experiment_parameters(hub, params['experiment']),
                   'model_params': lambda: recommender.get_default_params('model', params['model']),
                   'sampler_params': lambda: recommender.get_default_params('sampler', params['sampler']),
                   'servo_params': lambda: recommender.get_default_params('servo', params['servo']),
                   'error_params': lambda: recommender.load_experiment_parameters(hub, params['error']),
                   'models': lambda: recommender.list_classes('model'),
                   'samplers': lambda: recommender.list_classes('sampler'),
                   'servos': lambda: recommender.list_classes('servo')
                     }
        if target in targets:
            return targets[target]()

        elif target == 'history':
            hub = self.network.hubs[params['hub']]
            for sampler in hub.samplers.values():
                if sampler.id == params['id']:
                    break
            sampler.history = sampler.history.fillna(0)
            return sampler.history

        elif target == 'sampler':
            hub = self.network.hubs[params['hub']]
            for sampler in hub.samplers.values():
                if sampler.id == params['id']:
                    break
            return sampler

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

    def terminate(self, params):
        sampler = self.get('sampler', params)
        sampler.terminate()
