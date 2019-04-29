from flask import Blueprint, request
import json
from emergent.utilities import recommender, introspection
import pickle
import uuid
import logging as log

url_prefix = '/artiq'


def get_blueprint(core):
    blueprint = Blueprint('artiq', __name__)

    @blueprint.route('/connected')
    def connected():
        if hasattr(core, 'sequencer'):
            return '1'
        else:
            return '0'

    @blueprint.route("/handshake", methods=['GET', 'POST'])
    def handshake():
        if request.method == 'POST':
            log.info('Connecting to ARTIQ master.')
            core.start_artiq_client()
        return 'connected'

    @blueprint.route('/activate', methods=['POST'])
    def activate_sequence():
        core.sequencer.activate(request.get_json()['sequence'])

        return ''

    @blueprint.route('/sequence', methods=['GET', 'POST'])
    def sequence():
        s = core.sequencer
        if request.method == 'POST':
            s.steps = request.get_json()
            s.sequences[s.current_sequence] = s.steps
            s.save(s.current_sequence)
        return json.dumps(s.steps)

    @blueprint.route('/current_step', methods=['GET', 'POST'])
    def sequencer_step():
        if request.method == 'POST':
            core.sequencer.goto(request.get_json()['step'])
        return json.dumps(core.sequencer.current_step)

    @blueprint.route('/sequences', methods=['GET'])
    def get_sequences():
        return json.dumps(core.sequencer.sequences)

    @blueprint.route('/ttl')
    def get_ttls():
        return json.dumps(core.sequencer.ttl)

    @blueprint.route('/dac')
    def get_dacs():
        return json.dumps(core.sequencer.dac)

    @blueprint.route('/adc')
    def get_adcs():
        return json.dumps(core.sequencer.adc)

    @blueprint.route('/dds')
    def get_dds():
        return json.dumps(core.sequencer.dds)

    @blueprint.route('/store', methods=['POST'])
    def store_sequence():
        core.sequencer.store(request.get_json()['name'])

        return ''

    @blueprint.route('/delete', methods=['POST'])
    def delete_sequence(hub):
        core.sequencer.delete(request.get_json()['name'])

        return ''

    @blueprint.route('/data', methods = ['GET', 'POST'])
    def post_data():
        if not hasattr(core, 'artiq_data'):
            core.artiq_data = {}
        if request.method == 'GET':
            return json.dumps(core.artiq_data)
        elif request.method == 'POST':
            core.artiq_data = request.get_json()

    @blueprint.route('/pid')
    def get_pid():
        return str(uuid.uuid1())

    @blueprint.route('/run', methods=['GET', 'POST'])
    def submit():
        if not hasattr(core, 'artiq_link'):
            core.artiq_link = {}
        if request.method == 'POST':
            d = request.get_json()
            if d == {}:
                core.artiq_link = {}
            else:
                for key in d:
                    core.artiq_link[key] = d[key]
            return ''
        elif request.method == 'GET':
            return json.dumps(core.artiq_link)

    return blueprint
