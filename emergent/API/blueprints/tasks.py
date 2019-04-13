from flask import Blueprint, request, url_for
import json
url_prefix = ''


def get_blueprint(core):
    blueprint = Blueprint('tasks', __name__)

    @blueprint.route('/tasks', methods=['GET'])
    def tasks():
        return json.dumps(list(core.tasks.keys()))

    @blueprint.route('/tasks/<id>', methods=['GET', 'POST'])
    def task(id):
        if request.method == 'POST':
            params = request.get_json()
            core.tasks[id] = {}
            for x in ['start time', 'experiment', 'hub', 'id']:
                core.tasks[id][x] = params[x]
            core.emit('event', params)
        return json.dumps(core.tasks[id])

    return blueprint
