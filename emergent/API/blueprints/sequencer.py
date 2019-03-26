from flask import Blueprint, request
import json
from emergent.utilities import recommender, introspection
import pickle

url_prefix = '/hubs/<hub>/sequencer'

def get_blueprint(network):
    blueprint = Blueprint('sequencer', __name__)

    @blueprint.route('/sequence', methods=['GET', 'POST'])
    def hub_sequence(hub):
        s = network.hubs[hub].children['sequencer']
        if request.method == 'POST':
            s.steps = request.get_json()
        return json.dumps(s.steps)

    @blueprint.route('/ttl')
    def get_ttls(hub):
        s = network.hubs[hub].children['sequencer']
        return json.dumps(s.ttl)

    @blueprint.route('/dac')
    def get_dacs(hub):
        s = network.hubs[hub].children['sequencer']
        return json.dumps(s.dac)

    @blueprint.route('/adc')
    def get_adcs(hub):
        s = network.hubs[hub].children['sequencer']
        return json.dumps(s.adc)

    @blueprint.route('/dds')
    def get_dds(hub):
        s = network.hubs[hub].children['sequencer']
        return json.dumps(s.dds)

    @blueprint.route('/current_step', methods=['GET', 'POST'])
    def hub_sequencer_step(hub):
        s = network.hubs[hub].children['sequencer']
        if request.method == 'POST':
            s.goto(request.get_json()['step'])
        return json.dumps(s.current_step)


    return blueprint
