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
        return json.dumps(list(hub.options.keys()))

    @app.route('/hubs/<hub>/exec', methods=['POST'])
    def hub_exec(hub):
        ''' Runs a target function on the hub '''
        hub = network.hubs[hub]
        r = request.get_json()
        func = getattr(hub, r['method'])
        if 'args' in r:
            if 'kwargs' in r:
                func(*r['args'], **r['kwargs'])
            func(*r['args'])
        elif 'kwargs' in r:
            func(**r['kwargs'])
        else:
            func()
        return 'done'


    ''' Hub experiment endpoints '''
    @app.route('/hubs/<hub>/experiments')
    def list_experiments(hub):
        hub = network.hubs[hub]
        return json.dumps(introspection.list_experiments(hub))

    @app.route('/hubs/<hub>/experiments/<experiment>')
    def list_experiment_params(hub, experiment):
        sampler = request.args.get('sampler')
        model = request.args.get('model')
        hub = network.hubs[hub]
        params = load_all_experiment_parameters(hub, experiment, model, sampler)
        return json.dumps(params)

    @app.route('/hubs/<hub>/errors/<error>')
    def list_error_params(hub, error):
        hub = network.hubs[hub]
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


    ''' Hub sampler endpoints '''
    @app.route('/hubs/<hub>/samplers')
    def list_samplers(hub):
        hub = network.hubs[hub]
        ids = []
        for s in hub.samplers.values():
            ids.append(s.id)
        return json.dumps(ids)

    def get_sampler_by_id(hub, sampler_id):
            hub = network.hubs[hub]

            for s in hub.samplers.values():
                if s.id == sampler_id:
                    return s

    @app.route('/hubs/<hub>/samplers/<sampler_id>/data')
    def get_sampler_data(hub, sampler_id):
        obj = get_sampler_by_id(hub, sampler_id)
        if obj is None:
            return
        d = {'history': obj.history.to_json()}
        return json.dumps(d)

    @app.route('/hubs/<hub>/samplers/<sampler_id>/parameters')
    def get_sampler_parameters(hub, sampler_id):
        obj = get_sampler_by_id(hub, sampler_id)
        if obj is None:
            return
        hub = network.hubs[hub]

        d = {}
        d['experiment'] = {'name': obj.experiment.__name__, 'params': obj.experiment_params}
        if obj.algorithm is not None:
            d['algorithm'] = {'name': obj.algorithm.name, 'params': obj.algorithm_params}
        if obj.model is not None:
            d['model'] = {'name': obj.model.name, 'params': obj.model_params}
        d['limits'] = hub.range
        d['hub'] = hub.name
        d['inputs'] = obj.inputs

        return json.dumps(d)

    @app.route('/hubs/<hub>/samplers/<sampler_id>/active', methods=['GET', 'POST'])
    def check_sampler_active(hub, sampler_id):
        obj = get_sampler_by_id(hub, sampler_id)
        if obj is None:
            return
        if request.method == 'POST':
            obj.active = request.get_json()['status']
        return json.dumps(int(obj.active))

    @app.route('/hubs/<hub>/samplers/<sampler_id>/model')
    def get_sampler_model(hub, sampler_id):
        obj = get_sampler_by_id(hub, sampler_id)
        if obj is None:
            return
        if obj.model is not None:
            return pickle.dumps(obj.model)

    @app.route('/hubs/<hub>/samplers/<sampler_id>/algorithm')
    def get_sampler_algorithm(hub, sampler_id):
        obj = get_sampler_by_id(hub, sampler_id)
        if obj is None:
            return

        if obj.algorithm is not None:
            return pickle.dumps(obj.algorithm)

    def send_plot(fig):
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        return send_file(buf, mimetype='image/png')

    @app.route('/hubs/<hub>/samplers/<sampler_id>/plot/model')
    def plot_model(hub, sampler_id):
        obj = get_sampler_by_id(hub, sampler_id)
        if obj is None:
            return
        return send_plot(obj.model.plot())

    @app.route('/hubs/<hub>/samplers/<sampler_id>/plot/data')
    def plot_data(hub, sampler_id):
        obj = get_sampler_by_id(hub, sampler_id)
        if obj is None:
            return
        return send_plot(obj.algorithm.plot())

    @app.route('/hubs/<hub>/samplers/<sampler_id>/plot/history')
    def plot_history(hub, sampler_id):
        obj = get_sampler_by_id(hub, sampler_id)
        if obj is None:
            return

        t, points, costs, errors = obj.get_history(include_database=False)
        t = t.copy() - t[0]
        from emergent.utilities.plotting import plot_1D
        ax, fig = plot_1D(t,
                          -costs,
                          errors=errors,
                          xlabel='Time (s)',
                          ylabel=obj.experiment.__name__)
        return send_plot(fig)



    ''' Hub sequencing endpoints '''
    @app.route('/hubs/<hub>/switches')
    def hub_switches(hub):
        switches = network.hubs[hub].switches
        return json.dumps(list(switches.keys()))

    @app.route('/hubs/<hub>/sequencer/sequence', methods=['GET', 'POST'])
    def hub_sequence(hub):
        s = network.hubs[hub].children['sequencer']
        if request.method == 'POST':
            s.steps = request.get_json()
        return json.dumps(s.steps)

    @app.route('/hubs/<hub>/sequencer/current_step', methods=['GET', 'POST'])
    def hub_sequencer_step(hub):
        s = network.hubs[hub].children['sequencer']
        if request.method == 'POST':
            s.goto(request.get_json()['step'])
        return json.dumps(s.current_step)

    ''' Remote procedure call endpoints '''
    @app.route('/run', methods=['POST'])
    def run():
        from emergent.modules.sampler import Sampler

        settings = request.get_json()
        settings['hub'] = network.hubs[settings['hub']]
        settings['experiment']['instance'] = getattr(settings['hub'], settings['experiment']['name'])

        for x in ['model', 'sampler', 'servo']:
            if x in settings:
                settings[x]['instance'] = recommender.get_class(x, settings[x]['name'])
        sampler = Sampler('sampler', settings)
        sampler.id = str(uuid.uuid1())
        ''' Create task_panel task '''

        params = {'start time': datetime.datetime.now().isoformat(),
                  'experiment': settings['experiment']['name'],
                  'id': sampler.id,
                  'hub': sampler.hub.name}

        if 'algorithm' in settings:
            params['algorithm'] = settings['algorithm']['name']
        if hasattr(network, 'socketIO'):
            network.socketIO.emit('event', params)

        if 'trigger' in settings['process']:
            sampler.trigger = getattr(settings['hub'], settings['process']['trigger'])

        ''' Run process '''
        if settings['state'] == {} and settings['process']['type'] != 'run':
            log.warning('Please select at least one Input node.')
            return
        func = sampler._solve
        if settings['process']['type'] == 'run':
            func = sampler._run
        manager._run_thread(func, stoppable=False)

        return 'done'

    app.run(host=addr, debug=False, threaded=True)
