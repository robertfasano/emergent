from flask import Blueprint, request
import json
from emergent.utilities import recommender, introspection

url_prefix = '/hubs/<hub>/things/<thing>/knobs'

def get_blueprint(network):
    blueprint = Blueprint('knobs', __name__)

    ''' Thing endpoints '''
    @blueprint.route('/')
    def knobs(hub, thing):
        hub = network.hubs[hub]
        thing = hub.children[thing]
        return json.dumps(list(thing.children.keys()))

    @blueprint.route('/<knob>/options')
    def knob_options(hub, thing, knob):
        hub = network.hubs[hub]
        thing = hub.children[thing]
        knob = thing.children[knob]
        return json.dumps(list(knob.options.keys()))

    @blueprint.route('/<knob>/exec', methods=['POST'])
    def knob_exec(hub, thing, knob):
        ''' Runs a target function on the knob '''
        hub = network.hubs[hub]
        thing = hub.children[thing]
        knob = thing.children[knob]
        r = request.get_json()
        func = getattr(knob, r['method'])
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
