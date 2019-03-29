from flask import Blueprint, request, url_for
import json
import requests
import datetime
from emergent.utilities import recommender, introspection
from emergent.modules.sampler import Sampler
import uuid
import logging as log
from copy import deepcopy
url_prefix = ''

def prepare_sampler(settings, network):
    settings = deepcopy(settings)
    settings['hub'] = network.hubs[settings['hub']]
    settings['experiment']['instance'] = getattr(settings['hub'], settings['experiment']['name'])
    settings['range'] = settings['hub'].range.copy()
    for x in ['model', 'sampler', 'servo']:
        if x in settings:
            settings[x]['instance'] = recommender.get_class(x, settings[x]['name'])
    sampler = Sampler('sampler', settings)
    sampler.id = str(uuid.uuid1())

    ''' Load previously trained model if specified '''
    if 'model' in settings:
        if 'Weights' in settings['model']['params']:
            filename = network.path['data'] + '/' + settings['model']['params']['Weights'].split('.')[0]
            sampler.model._import(filename)

    if 'algorithm' in settings:
        params['algorithm'] = settings['algorithm']['name']

    if 'trigger' in settings['process']:
        sampler.trigger = getattr(settings['hub'], settings['process']['trigger'])

    return sampler

def get_blueprint(network):
    blueprint = Blueprint('rpc', __name__)

    @blueprint.route('/run', methods=['POST'])
    def run():
        settings = request.get_json()
        sampler = prepare_sampler(settings, network)
        ''' Create task_panel task '''
        params = {'start time': datetime.datetime.now().isoformat(),
                  'experiment': settings['experiment']['name'],
                  'id': sampler.id,
                  'hub': sampler.hub.name}
        requests.post(network.url+url_for('tasks.task', id=sampler.id), json=params)


        ''' Run process '''
        if settings['state'] == {} and settings['process']['type'] != 'run':
            log.warning('Please select at least one Knob.')
            return
        func = sampler._solve
        if settings['process']['type'] == 'measure':
            func = sampler._run
        network.manager._run_thread(func, stoppable=False)

        return 'done'

    return blueprint
