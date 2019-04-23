from flask import Blueprint, request
import json
from emergent.utilities import recommender, introspection
import pickle
import uuid
import os

url_prefix = '/optimize'

def get_blueprint(core):
    blueprint = Blueprint('optimize', __name__)

    @blueprint.route('/save', methods=['POST'])
    def save():
        params = request.get_json()
        path = core.path['pipelines']
        if not os.path.exists(path):
            os.makedirs(path)
        with open(path+params['name']+'.json', 'w') as file:
            json.dump(params['pipeline'], file, indent=2)
        return ''

    @blueprint.route('/pipelines/<name>')
    def load(name):
        path = core.path['pipelines']
        if not os.path.exists(path):
            os.makedirs(path)
        with open(path+name+'.json', 'r') as file:
            pipe = json.load(file)
        return json.dumps(pipe)

    @blueprint.route('/pipelines')
    def get_saved():
        path = core.path['pipelines']
        if not os.path.exists(path):
            os.makedirs(path)

        names = []
        for name in os.listdir(path):
            names.append(name.split('.json')[0])

        return json.dumps(names)

    return blueprint
