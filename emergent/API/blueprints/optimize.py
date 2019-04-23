from flask import Blueprint, request
import json
from emergent.utilities import recommender, introspection
import pickle
import uuid
import os
from emergent.pipeline import Pipeline
from threading import Thread

url_prefix = '/optimize'

def get_blueprint(core):
    blueprint = Blueprint('optimize', __name__)

    @blueprint.route('/save', methods=['POST'])
    def save():
        params = request.get_json()
        path = core.path['pipelines']
        if not os.path.exists(path):
            os.makedirs(path)
        with open(path+params['name']+'.json', 'w') as file:
            json.dump(params['pipeline'], file, indent=2)
        return ''

    @blueprint.route('/pipelines/<name>')
    def load(name):
        path = core.path['pipelines']
        if not os.path.exists(path):
            os.makedirs(path)
        with open(path+name+'.json', 'r') as file:
            pipe = json.load(file)
        return json.dumps(pipe)

    @blueprint.route('/pipelines')
    def get_saved():
        path = core.path['pipelines']
        if not os.path.exists(path):
            os.makedirs(path)

        names = []
        for name in os.listdir(path):
            names.append(name.split('.json')[0])

        return json.dumps(names)

    def range_dict_to_tuple(d):
        new_dict = {}
        for device in d:
            new_dict[device] = {}
            for knob in d[device]:
                new_dict[device][knob] = (d[device][knob]['min'], d[device][knob]['max'])
        return new_dict

    @blueprint.route('/run', methods=['POST'])
    def run():
        print('Creating new pipeline.')

        if request.method == 'POST':
            payload = request.get_json()
            hub = core.hubs[payload['hub']]
            experiment = getattr(hub, payload['experiment'])
            bounds = range_dict_to_tuple(payload['range'])
            pipe = Pipeline(payload['state'], bounds, experiment)
            pipe.from_json(payload['blocks'])

            if not hasattr(hub, 'pipelines'):
                hub.pipelines = []
            hub.pipelines.append(pipe)

            Thread(target=pipe.run).start()
        return ''

    return blueprint
