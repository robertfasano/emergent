from flask import Blueprint, request
import json
from emergent.utilities import recommender, introspection
import pickle
import uuid
import logging as log

url_prefix = '/artiq'


def get_blueprint(core):
    blueprint = Blueprint('artiq', __name__)

    @blueprint.route("/handshake", methods=['GET', 'POST'])
    def handshake():
        if request.method == 'POST':
            log.info('Connecting to ARTIQ master.')
            core.start_artiq_client()
        return 'connected'

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
