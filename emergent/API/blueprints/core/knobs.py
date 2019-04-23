from flask import Blueprint, request
import json
from emergent.utilities import recommender, introspection

url_prefix = '/hubs/<hub>/devices/<device>/knobs'

def get_blueprint(core):
    blueprint = Blueprint('knobs', __name__)

    ''' Device endpoints '''
    @blueprint.route('/')
    def knobs(hub, device):
        hub = core.hubs[hub]
        device = hub.devices[device]
        return json.dumps(list(device.knobs.keys()))

    @blueprint.route('/<knob>/options')
    def knob_options(hub, device, knob):
        hub = core.hubs[hub]
        device = hub.devices[device]
        knob = device.knobs[knob]
        return json.dumps(list(knob.options.keys()))

    @blueprint.route('/<knob>/exec', methods=['POST'])
    def knob_exec(hub, device, knob):
        ''' Runs a target function on the knob '''
        hub = core.hubs[hub]
        device = hub.devices[device]
        knob = device.knobs[knob]
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
