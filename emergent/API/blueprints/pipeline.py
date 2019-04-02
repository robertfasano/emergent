from flask import Blueprint, request
import json
from emergent.utilities import recommender, introspection
import pickle
import uuid

url_prefix = '/hubs/<hub>/pipeline'

def get_blueprint(network):
    blueprint = Blueprint('pipeline', __name__)

    @blueprint.route('/new', methods=['POST'])
    def new_pipeline(hub):
        print('Creating new pipeline.')
        hub = network.hubs[hub]
        from emergent.pipeline import Pipeline, Source

        if request.method == 'POST':
            payload = request.get_json()

            experiment = getattr(hub, payload['experiment'])
            source = Source(payload['state'], payload['range'], experiment, payload['params'])

            pipe = Pipeline(payload['state'], network)
            pipe.add_source(source)
            pipe.add_blocks(request.get_json()['blocks'])

            if not hasattr(hub, 'pipelines'):
                hub.pipelines = []
            hub.pipelines.append(pipe)

            pipe.run()
        return ''


    return blueprint
