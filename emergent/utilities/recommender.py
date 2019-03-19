''' This module implements methods for parameter persistence, allowing the following
    quantities to be saved/loaded to/from file:

    * Experiment parameters
    * Algorithm parameters for each experiment
    * Default algorithm to use for each experiment

    It also implements methods allowing algorithm/servo instances to be constructed
    and returned by name, as well as listing all algorithms/servos included in the
    __init__.py files in the emergent/optimizers and emergent/servos folders
    respectively.
'''
import importlib
import json
import inspect

def save_default_algorithm(hub, experiment_name, algorithm_name):
    params_filename = hub.network.path['params'] + '%s.%s.txt'%(hub.name, experiment_name)
    with open(params_filename, 'r') as file:
        params = json.load(file)
    params['algorithm']['default'] = algorithm_name
    with open(params_filename, 'w') as file:
        json.dump(params, file)


def get_default_algorithm(hub, experiment_name):
    params_filename = hub.network.path['params'] + '%s.%s.txt'%(hub.name, experiment_name)
    with open(params_filename, 'r') as file:
        params = json.load(file)
    try:
        return get_class('algorithm', params['algorithm']['default'])
    except KeyError:
        save_default_algorithm(hub, experiment_name, 'GridSearch')
        return get_class('algorithm', 'GridSearch')

def get_default_params(module, name):
    if name == 'None':
        return {}
    module_name = {'sampler': 'emergent.samplers', 'model': 'emergent.models',
                   'algorithm': 'optimizers', 'servo': 'emergent.servos'}[module]
    instance = getattr(importlib.import_module(module_name), name)()
    params = instance.params
    params_dict = {}
    for p in params:
        params_dict[p] = params[p].value

    return params_dict

def get_default_experiment_params(hub, experiment_name):
        experiment = getattr(hub, experiment_name)
        args = inspect.signature(experiment).parameters
        args = list(args.items())
        d = {}
        for a in args:
            if a[0] != 'params':
                continue
            d = str(a[1]).split('=')[1]
            d = json.loads(d.replace("'", '"'))
        return d

def get_class(module, name):
    if name == 'None':
        return None
    module_name = {'sampler': 'emergent.samplers', 'model': 'emergent.models',
                   'algorithm': 'optimizers', 'servo': 'emergent.servos'}[module]
    instance = getattr(importlib.import_module(module_name), name)()
    return instance

def list_classes(module_type):
    module_name = {'sampler': 'emergent.samplers', 'model': 'emergent.models',
                   'algorithm': 'optimizers', 'servo': 'emergent.servos'}[module_type]
    module = importlib.import_module(module_name)
    names = []
    for a in dir(module):
        if '__' not in a:
            inst = getattr(module, a)
            if inspect.isclass(inst):
                names.append(inst().name)
    return names

def load_algorithm_parameters(hub, experiment_name, algorithm_name, module_type, default = False):
    ''' Looks for algorithm parameters in the parameterfile for the experiment. If none exist,
        get them from the default algorithm parameters.

        Args:
            hub (Hub): a node whose experiment we're about to run
            experiment_name (str)
            algorithm_name (str)
            default (bool)
            module_type (str): either 'algorithm' or 'servo'
    '''

    ''' Look for relevant parameters in the json file in the network's params directory '''
    params_filename = hub.network.path['params'] + '%s.%s.txt'%(hub.name, experiment_name)
    if module_type in ['algorithm', 'servo']:
        key = 'algorithm'
    else:
        key = 'sampler'
    if not default:
        try:
            ''' Load params from file '''
            with open(params_filename, 'r') as file:
                params = json.load(file)

            ''' See if the algorithm we're interested in has saved parameters'''
            if key not in params:
                params[key] = {}
            if algorithm_name in params[key]:
                return params[key][algorithm_name]
            else:
                ''' Load the default parameters and add them to file '''
                d = get_default_params(module_type, algorithm_name)
                with open(params_filename, 'r') as file:
                    params = json.load(file)
                if key not in params:
                    params[key] = {}
                params[key][algorithm_name] = d
                with open(params_filename, 'w') as file:
                    json.dump(params, file)
                return d
        except OSError:
            pass
    ''' If file does not exist, then load from introspection '''
    default_algo = {'algorithm': 'GridSearch', 'servo': 'PID', 'sampler': 'GridSampling'}[module_type]
    params = {'experiment': {}, key: {'default': default_algo}}
    params[key][algorithm_name] = get_default_params(module_type, algorithm_name)

    with open(params_filename, 'w') as file:
        json.dump(params, file)

    return params[key][algorithm_name]

def load_all_error_parameters(hub, experiment_name, servo_name):
    ''' Looks for algorithm parameters in the parameterfile for the experiment. If none exist,
        get them from the default algorithm parameters.

        Args:
            hub (Hub): a node whose experiment we're about to run
            experiment_name (str)
            servo_name (str)
    '''

    ''' Look for relevant parameters in the json file in the network's params directory '''

    ''' TO ADD: get default params only as an option'''
    params_filename = hub.network.path['params'] + '%s.%s.txt'%(hub.name, experiment_name)

    ''' Try to open the params file '''
    try:
        with open(params_filename, 'r') as file:
            params = json.load(file)

    except OSError:
        ''' File doesn't yet exist; let's prepare a default file '''
        params = {'error': {}}
        params['servo'] = {'default': servo_name}
        params['servo'][servo_name] = get_default_params('servo', servo_name)
        params['error'] = get_default_experiment_params(hub, experiment_name)

    ''' If the file exists, let's try to access each parameter we need '''
    p = {'error': params['error'], 'servo': {}}

    if servo_name not in params['servo']:
        params['servo'][servo_name] = get_default_params('servo', servo_name)
    p['servo'][servo_name] = params['servo'][servo_name]


    ''' Save (possibly) updated params dict to file '''
    with open(params_filename, 'w') as file:
        json.dump(params, file)

    return p

def load_all_experiment_parameters(hub, experiment_name, model_name=None, sampler_name=None):
    ''' Looks for algorithm parameters in the parameterfile for the experiment. If none exist,
        get them from the default algorithm parameters.

        Args:
            hub (Hub): a node whose experiment we're about to run
            experiment_name (str)
            algorithm_name (str)
            model_name (str)
    '''

    ''' Look for relevant parameters in the json file in the network's params directory '''

    ''' TO ADD: get default params only as an option'''
    params_filename = hub.network.path['params'] + '%s.%s.txt'%(hub.name, experiment_name)

    ''' Try to open the params file '''
    try:
        with open(params_filename, 'r') as file:
            params = json.load(file)

    except OSError:
        ''' File doesn't yet exist; let's prepare a default file '''
        params = {'experiment': {}}
        if sampler_name is not None:
            params['sampler'] = {'default': sampler_name}
            params['sampler'][sampler_name] = get_default_params('sampler', sampler_name)
        if model_name is not None:
            params['model'] = {'default': model_name}
            params['model'][model_name] = get_default_params('model', model_name)

        params['experiment'] = get_default_experiment_params(hub, experiment_name)

    ''' If the file exists, let's try to access each parameter we need '''
    p = {'experiment': params['experiment']}


    if model_name is not None:
        p['model'] = {}
        if 'model' not in params:
            params['model'] = {}
        if model_name not in params['model']:
            params['model'][model_name] = get_default_params('model', model_name)
        p['model'][model_name] = params['model'][model_name]

    if sampler_name is not None:
        p['sampler'] = {}
        if 'sampler' not in params:
            params['sampler'] = {}
        if sampler_name not in params['sampler']:
            params['sampler'][sampler_name] = get_default_params('sampler', sampler_name)
        p['sampler'][sampler_name] = params['sampler'][sampler_name]


    ''' Save (possibly) updated params dict to file '''
    with open(params_filename, 'w') as file:
        json.dump(params, file)

    return p

def load_experiment_parameters(hub, experiment_name, default = False):
    ''' Looks for algorithm parameters in the parameterfile for the experiment. If none exist,
        get them from the default algorithm parameters and save a new parameterfile.

        Args:
            hub (Hub): a node whose experiment we're about to run
            experiment_name (str)
            default (bool)
    '''

    ''' Look for relevant parameters in the json file in the network's params directory '''
    params_filename = hub.network.path['params'] + '%s.%s.txt'%(hub.name, experiment_name)

    if not default:
        try:
            ''' Load params from file '''
            with open(params_filename, 'r') as file:
                params = json.load(file)
            if 'experiment' not in params:
                raise OSError
            if params['experiment'] == {}:
                raise OSError
            if 'cycles per sample' not in params['experiment']:
                params['experiment']['cycles per sample'] = 1
            return params['experiment']
        except OSError:
            pass
    ''' If file does not exist, then load from introspection '''
    params = {'experiment': {}, 'algorithm': {'default': 'GridSearch'}}

    ''' load experiment params '''
    experiment = getattr(hub, experiment_name)
    args = inspect.signature(experiment).parameters
    args = list(args.items())
    d = {}
    for a in args:
        if a[0] != 'params':
            continue
        d = str(a[1]).split('=')[1]
        d = json.loads(d.replace("'", '"'))
    params['experiment'] = d

    with open(params_filename, 'w') as file:
        json.dump(params, file)

    if 'cycles per sample' not in params['experiment']:
        params['experiment']['cycles per sample'] = 1
    return params['experiment']
