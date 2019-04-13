from flask import Blueprint, request, url_for
import json
import requests
import datetime
from emergent.utilities import recommender, introspection
from emergent.modules.sampler import Sampler
import logging as log
from copy import deepcopy
url_prefix = ''

def prepare_sampler(settings, core):
    settings = deepcopy(settings)
    settings['hub'] = core.hubs[settings['hub']]
    settings['range'] = settings['hub'].range.copy()
    sampler = Sampler('sampler', settings)

    return sampler

def get_blueprint(core):
    blueprint = Blueprint('rpc', __name__)

    @blueprint.route('/run', methods=['POST'])
    def run():
        settings = request.get_json()
        sampler = prepare_sampler(settings, core)

        ''' Create task_panel task '''
        params = {'start time': datetime.datetime.now().isoformat(),
                  'experiment': settings['experiment']['name'],
                  'id': sampler.id,
                  'hub': sampler.hub.name}
        if 'algorithm' in settings:
            params['algorithm'] = settings['algorithm']['name']
        requests.post(core.url+url_for('tasks.task', id=sampler.id), json=params)


        ''' Run process '''
        if settings['state'] == {} and settings['process']['type'] != 'run':
            log.warning('Please select at least one Knob.')
            return
        func = sampler._solve
        if settings['process']['type'] == 'measure':
            func = sampler._run
        core.manager._run_thread(func, stoppable=False)

        return 'done'

    return blueprint
