from flask import Blueprint, request
import json
from emergent.utilities import recommender, introspection
import pickle

url_prefix = '/hubs'

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

def get_blueprint(network):
    blueprint = Blueprint('hubs', __name__)

    @blueprint.route('/')
    def list_hubs():
        hubs = list(network.hubs.keys())
        links = []
        html = ''
        for hub in hubs:
            new = '<a href=%s>hub</a>'%hub
            links.append(new)
            html += new
        # return json.dumps(links)
        return html

    @blueprint.route('/<hub>')
    def list_hub_endpoints(hub):
        endpoints = ['experiments', 'state', 'range', 'options']
        links = []
        html = ''
        for endpoint in endpoints:
            new = '<p><a href=%s/%s>%s</a></p>'%(hub, endpoint, endpoint)
            links.append(new)
            html += new
        # return json.dumps(links)
        return html

    @blueprint.route('/<hub>/state', methods = ['GET', 'POST'])
    def hub_state(hub):
        hub = network.hubs[hub]
        if request.method == 'POST':
            state = request.get_json()
            hub.actuate(state, send_over_p2p=False)
        return json.dumps(hub.state)

    @blueprint.route('/<hub>/range', methods = ['GET', 'POST'])
    def hub_range(hub):
        hub = network.hubs[hub]
        if request.method == 'POST':
            range = request.get_json()
            network.set_range({hub.name: range})
        return json.dumps(hub.range)

    @blueprint.route('/<hub>/options')
    def hub_options(hub):
        hub = network.hubs[hub]
        return json.dumps(list(hub.options.keys()))

    @blueprint.route('/<hub>/exec', methods=['POST'])
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
    @blueprint.route('/<hub>/experiments')
    def list_experiments(hub):
        hub = network.hubs[hub]
        return json.dumps(introspection.list_experiments(hub))

    @blueprint.route('/<hub>/experiments/<experiment>')
    def list_experiment_params(hub, experiment):
        sampler = request.args.get('sampler')
        model = request.args.get('model')
        hub = network.hubs[hub]
        params = load_all_experiment_parameters(hub, experiment, model, sampler)
        return json.dumps(params)

    @blueprint.route('/<hub>/errors/<error>')
    def list_error_params(hub, error):
        hub = network.hubs[hub]
        servo = request.args.get('servo')
        params = recommender.load_all_error_parameters(hub, error, servo)
        return json.dumps(params)

    @blueprint.route('/<hub>/errors')
    def list_errors(hub):
        hub = network.hubs[hub]
        return json.dumps(introspection.list_errors(hub))

    @blueprint.route('/<hub>/triggers')
    def list_triggers(hub):
        hub = network.hubs[hub]
        return json.dumps(introspection.list_triggers(hub))


    ''' Hub sampler endpoints '''
    @blueprint.route('/<hub>/samplers')
    def list_samplers(hub):
        hub = network.hubs[hub]
        ids = []
        for s in hub.samplers.values():
            ids.blueprintend(s.id)
        return json.dumps(ids)

    def get_sampler_by_id(hub, sampler_id):
            hub = network.hubs[hub]

            for s in hub.samplers.values():
                if s.id == sampler_id:
                    return s

    @blueprint.route('/<hub>/samplers/<sampler_id>/data')
    def get_sampler_data(hub, sampler_id):
        obj = get_sampler_by_id(hub, sampler_id)
        if obj is None:
            return
        d = {'history': obj.history.to_json()}
        return json.dumps(d)

    @blueprint.route('/<hub>/samplers/<sampler_id>/parameters')
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

    @blueprint.route('/<hub>/samplers/<sampler_id>/active', methods=['GET', 'POST'])
    def check_sampler_active(hub, sampler_id):
        obj = get_sampler_by_id(hub, sampler_id)
        if obj is None:
            return
        if request.method == 'POST':
            obj.active = request.get_json()['status']
        return json.dumps(int(obj.active))

    @blueprint.route('/<hub>/samplers/<sampler_id>/model')
    def get_sampler_model(hub, sampler_id):
        obj = get_sampler_by_id(hub, sampler_id)
        if obj is None:
            return
        if obj.model is not None:
            return pickle.dumps(obj.model)

    @blueprint.route('/<hub>/samplers/<sampler_id>/algorithm')
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

    @blueprint.route('/<hub>/samplers/<sampler_id>/plot/model')
    def plot_model(hub, sampler_id):
        obj = get_sampler_by_id(hub, sampler_id)
        if obj is None:
            return
        return send_plot(obj.model.plot())

    @blueprint.route('/<hub>/samplers/<sampler_id>/plot/data')
    def plot_data(hub, sampler_id):
        obj = get_sampler_by_id(hub, sampler_id)
        if obj is None:
            return
        return send_plot(obj.algorithm.plot())

    @blueprint.route('/<hub>/samplers/<sampler_id>/plot/history')
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
    @blueprint.route('/<hub>/switches')
    def hub_switches(hub):
        switches = network.hubs[hub].switches
        return json.dumps(list(switches.keys()))

    @blueprint.route('/<hub>/sequencer/sequence', methods=['GET', 'POST'])
    def hub_sequence(hub):
        s = network.hubs[hub].children['sequencer']
        if request.method == 'POST':
            s.steps = request.get_json()
        return json.dumps(s.steps)

    @blueprint.route('/<hub>/sequencer/current_step', methods=['GET', 'POST'])
    def hub_sequencer_step(hub):
        s = network.hubs[hub].children['sequencer']
        if request.method == 'POST':
            s.goto(request.get_json()['step'])
        return json.dumps(s.current_step)


    return blueprint
