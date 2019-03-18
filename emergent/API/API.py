from flask import Flask, make_response, request, send_file
import numpy as np
import pickle
import pandas as pd
import json
import io
import uuid
import datetime
import matplotlib.pyplot as plt
from emergent.utilities import recommender, introspection
from emergent.utilities.containers import DataDict
from emergent.utilities.networking import get_address
from emergent.modules import ProcessHandler
import importlib, inspect

manager = ProcessHandler()
def load_all_experiment_parameters(hub, experiment_name, model_name = None, sampler_name = None):
    ''' Looks for algorithm parameters in the parameterfile for the experiment. If none exist,
        get them from the default algorithm parameters.

        Args:
            hub (Hub): a node whose experiment we're about to run
            experiment_name (str)
            algorithm_name (str)
            model_name (str)
    '''

    ''' Look for relevant parameters in the json file in the network's params directory '''

    params_filename = hub.network.path['params'] + '%s.%s.txt'%(hub.name, experiment_name)
    params = {'experiment': {}}
    params['experiment'] = recommender.get_default_experiment_params(hub, experiment_name)
    p = {'experiment': params['experiment']}

    if model_name is not None:
        p['model'] = {}
        if 'model' not in params:
            params['model'] = {}
        if model_name not in params['model']:
            params['model'][model_name] = recommender.get_default_params('model', model_name)
        p['model'][model_name] = params['model'][model_name]

    if sampler_name is not None:
        p['sampler'] = {}
        if 'sampler' not in params:
            params['sampler'] = {}
        if sampler_name not in params['sampler']:
            params['sampler'][sampler_name] = recommender.get_default_params('sampler', sampler_name)
        p['sampler'][sampler_name] = params['sampler'][sampler_name]

    return p

def serve(network, addr):
    app = Flask(__name__)

    blueprints=importlib.import_module('emergent.API.blueprints')
    for item in inspect.getmembers(blueprints, inspect.ismodule):
        blueprint = item[1].get_blueprint(network)
        app.register_blueprint(blueprint, url_prefix=item[1].url_prefix)

    @app.route("/")
    def hello():
        return "EMERGENT API"

    @app.route("/handshake", methods=['GET', 'POST'])
    def handshake():
        if request.method == 'POST':
            network.start_flask_socket_server()
        return 'connected'

    ''' Network endpoints '''
    @app.route('/state', methods=['GET', 'POST'])
    def state():
        if request.method == 'POST':
            state = request.get_json()
            network.actuate(state, send_over_p2p=False)
        return json.dumps(network.state())

    @app.route('/range', methods=['GET', 'POST'])
    def range():
        if request.method == 'POST':
            range = request.get_json()
            network.set_range(range)
        return json.dumps(network.range())


    app.run(host=addr, debug=False, threaded=True)
