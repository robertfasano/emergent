from flask import Blueprint, request, url_for
import json
url_prefix = ''


def get_blueprint(network):
    blueprint = Blueprint('tasks', __name__)

    @blueprint.route('/tasks', methods=['GET'])
    def tasks():
        return json.dumps(list(network.tasks.keys()))

    @blueprint.route('/tasks/<id>', methods=['GET', 'POST'])
    def task(id):
        if request.method == 'POST':
            params = request.get_json()
            network.tasks[id] = {}
            for x in ['start time', 'experiment', 'hub', 'id']:
                network.tasks[id][x] = params[x]
            if hasattr(network, 'socketIO'):
                network.socketIO.emit('event', params)
        return json.dumps(network.tasks[id])

    return blueprint
