from flask import Blueprint, request
import json
from emergent.utilities import recommender, introspection
import pickle
import uuid

url_prefix = '/hubs/<hub>/pipeline'

def get_blueprint(network):
    blueprint = Blueprint('pipeline', __name__)

    def range_dict_to_tuple(d):
        new_dict = {}
        for thing in d:
            new_dict[thing] = {}
            for knob in d[thing]:
                new_dict[thing][knob] = (d[thing][knob]['min'], d[thing][knob]['max'])
        return new_dict

    @blueprint.route('/new', methods=['POST'])
    def new_pipeline(hub):
        print('Creating new pipeline.')
        hub = network.hubs[hub]
        from emergent.pipeline import Pipeline, Source

        if request.method == 'POST':
            payload = request.get_json()
            experiment = getattr(hub, payload['experiment'])
            bounds = range_dict_to_tuple(payload['range'])
            pipe = Pipeline(payload['state'], bounds, experiment)
            pipe.from_json(request.get_json()['blocks'])

            if not hasattr(hub, 'pipelines'):
                hub.pipelines = []
            hub.pipelines.append(pipe)

            pipe.run()
        return ''


    return blueprint
