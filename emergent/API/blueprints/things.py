from flask import Blueprint, request
import json
from emergent.utilities import recommender, introspection

url_prefix = '/hubs/<hub>/things'

def get_blueprint(network):
    blueprint = Blueprint('things', __name__)

    ''' Thing endpoints '''
    @blueprint.route('/')
    def things(hub):
        hub = network.hubs[hub]
        return json.dumps(list(hub.children.keys()))

    @blueprint.route('/<thing>/options')
    def thing_options(hub, thing):
        hub = network.hubs[hub]
        thing = hub.children[thing]
        return json.dumps(list(thing.options.keys()))

    @blueprint.route('/<thing>/exec', methods=['POST'])
    def thing_exec(hub, thing):
        ''' Runs a target function on the hub '''
        hub = network.hubs[hub]
        thing = hub.children[thing]
        r = request.get_json()
        func = getattr(thing, r['method'])
        if 'args' in r:
            if 'kwargs' in r:
                func(*r['args'], **r['kwargs'])
            func(*r['args'])
        elif 'kwargs' in r:
            func(**r['kwargs'])
        else:
            func()
        return 'done'

    return blueprint
