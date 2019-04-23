from flask import Blueprint, request
import json
from emergent.utilities import recommender, introspection

url_prefix = '/hubs/<hub>/devices'

def get_blueprint(core):
    blueprint = Blueprint('devices', __name__)

    ''' Device endpoints '''
    @blueprint.route('/')
    def devices(hub):
        hub = core.hubs[hub]
        return json.dumps(list(hub.devices.keys()))

    @blueprint.route('/<device>/options')
    def device_options(hub, device):
        hub = core.hubs[hub]
        device = hub.devices[device]
        return json.dumps(list(device.options.keys()))

    @blueprint.route('/<device>/exec', methods=['POST'])
    def device_exec(hub, device):
        ''' Runs a target function on the hub '''
        hub = core.hubs[hub]
        device = hub.devices[device]
        r = request.get_json()
        func = getattr(device, r['method'])
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
