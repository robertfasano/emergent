from flask import Flask, make_response, request
import numpy as np
import pickle
import pandas as pd
import json
from emergent.utilities import recommender, introspection
from emergent.utilities.containers import DataDict
from emergent.utilities.networking import get_address

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

    @app.route("/")
    def hello():
        return "EMERGENT API"

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



    ''' Introspection endpoints '''
    @app.route('/models')
    def models():
        return json.dumps(recommender.list_classes('model'))

    @app.route('/samplers')
    def samplers():
        return json.dumps(recommender.list_classes('sampler'))

    @app.route('/servos')
    def servos():
        return json.dumps(recommender.list_classes('servo'))




    ''' Hub endpoints '''
    @app.route('/hubs')
    def list_hubs():
        return json.dumps(list(network.hubs.keys()))

    @app.route('/hubs/<hub>')
    def list_hub_endpoints(hub):
        endpoints = ['experiments', 'state', 'range']
        return json.dumps(endpoints)

    @app.route('/hubs/<hub>/state', methods = ['GET', 'POST'])
    def hub_state(hub):
        hub = network.hubs[hub]
        if request.method == 'POST':
            state = request.get_json()
            hub.actuate(state, send_over_p2p=False)
        return json.dumps(hub.state)

    @app.route('/hubs/<hub>/range', methods = ['GET', 'POST'])
    def hub_range(hub):
        hub = network.hubs[hub]
        if request.method == 'POST':
            range = request.get_json()
            network.set_range({hub.name: range})
        return json.dumps(hub.range)

    @app.route('/hubs/<hub>/options')
    def hub_options(hub):
        hub = network.hubs[hub]
        return json.dumps(hub.options)



    ''' Hub experiment endpoints '''
    @app.route('/hubs/<hub>/experiments')
    def list_experiments(hub):
        hub = network.hubs[hub]
        return json.dumps(introspection.list_experiments(hub))

    @app.route('/hubs/<hub>/experiments/<experiment>')
    def list_experiment_params(hub, experiment):
        sampler = request.args.get('sampler')
        model = request.args.get('model')
        hub = network.hubs['hub']
        params = load_all_experiment_parameters(hub, experiment, model, sampler)
        return json.dumps(params)

    @app.route('/hubs/<hub>/errors/<error>')
    def list_error_params(hub, error):
        hub = network.hubs['hub']
        servo = request.args.get('servo')
        params = recommender.load_all_error_parameters(hub, error, servo)
        return json.dumps(params)

    @app.route('/hubs/<hub>/errors')
    def list_errors(hub):
        hub = network.hubs[hub]
        return json.dumps(introspection.list_errors(hub))

    @app.route('/hubs/<hub>/triggers')
    def list_triggers(hub):
        hub = network.hubs[hub]
        return json.dumps(introspection.list_triggers(hub))

    app.run(host=addr, debug=False, threaded=True)
