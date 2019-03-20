from flask import Blueprint, request, url_for
import json
import datetime
from emergent.utilities import recommender, introspection
from emergent.modules.sampler import Sampler
import uuid
import logging as log
url_prefix = ''


def get_blueprint(network):
    blueprint = Blueprint('rpc', __name__)

    @blueprint.route('/run', methods=['POST'])
    def run():
        settings = request.get_json()
        settings['hub'] = network.hubs[settings['hub']]
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

        import requests
        requests.post(network.url+url_for('tasks.task', id=sampler.id), json=params)

        if 'trigger' in settings['process']:
            sampler.trigger = getattr(settings['hub'], settings['process']['trigger'])
        ''' Run process '''
        if settings['state'] == {} and settings['process']['type'] != 'measure':
            log.warning('Please select at least one Input node.')
            return
        func = sampler._solve
        if settings['process']['type'] == 'measure':
            func = sampler._run
        network.manager._run_thread(func, stoppable=False)

        return 'done'

    return blueprint
