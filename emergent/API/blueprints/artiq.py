from flask import Blueprint, request
import json
from emergent.utilities import recommender, introspection
import pickle
import uuid

url_prefix = '/artiq'


def get_blueprint(network):
    blueprint = Blueprint('artiq', __name__)

    @blueprint.route("/handshake", methods=['GET', 'POST'])
    def handshake():
        if request.method == 'POST':
            print('Connecting to ARTIQ master.')
            network.start_artiq_client()
        return 'connected'

    @blueprint.route('/data', methods = ['GET', 'POST'])
    def post_data():
        if not hasattr(network, 'artiq_data'):
            network.artiq_data = {}
        if request.method == 'GET':
            return json.dumps(network.artiq_data)
        elif request.method == 'POST':
            network.artiq_data = request.get_json()

    @blueprint.route('/pid')
    def get_pid():
        return str(uuid.uuid1())

    @blueprint.route('/run', methods=['GET', 'POST'])
    def submit():
        if not hasattr(network, 'artiq_link'):
            network.artiq_link = {}
        if request.method == 'POST':
            network.artiq_link = request.get_json()
            return ''
        elif request.method == 'GET':
            return json.dumps(network.artiq_link)

    return blueprint
