import importlib
import json
import inspect

def get_default_algorithm(hub, experiment_name):
    params_filename = hub.network.params_path + '%s.%s.txt'%(hub.name, experiment_name)
    with open(params_filename, 'r') as file:
        params = json.load(file)
    return get_algorithm(params['algorithm']['default'])

def get_default_algorithm_params(name):
    instance = get_algorithm(name)
    params = instance.params
    algo_params = {}
    for p in params:
        algo_params[p] = params[p].value

    return algo_params

def get_algorithm(name):
    ''' Returns an instance of an algorithm. '''
    return getattr(importlib.__import__('optimizers'), name)()

def get_default_servo_params(name):
    instance = get_servo(name)
    params = instance.params
    servo_params = {}
    for p in params:
        servo_params[p] = params[p].value

    return servo_params

def get_servo(name):
    ''' Returns an instance of a servo '''
    return getattr(importlib.__import__('servos'), name)()

def list_algorithms():
    module = importlib.__import__('optimizers')
    names = []
    for a in dir(module):
        if '__' not in a:
            inst = getattr(module, a)
            names.append(inst().name)
    return names

def list_servos():
    module = importlib.__import__('servos')
    names = []
    for a in dir(module):
        if '__' not in a:
            inst = getattr(module, a)
            names.append(inst().name)
    return names

def load_algorithm_parameters(hub, experiment_name, algorithm_name, default = False):
    ''' Looks for algorithm parameters in the parameterfile for the experiment. If none exist,
        get them from the default algorithm parameters.

        Args:
            hub (Hub): a node whose experiment we're about to run
            experiment_name (str)
            algorithm_name (str)
            default (bool)
    '''

    ''' Look for relevant parameters in the json file in the network's params directory '''
    params_filename = hub.network.params_path + '%s.%s.txt'%(hub.name, experiment_name)
    if not default:
        try:
            ''' Load params from file '''
            with open(params_filename, 'r') as file:
                params = json.load(file)

            ''' See if the algorithm we're interested in has saved parameters'''
            if algorithm_name in params['algorithm']:
                return params['algorithm'][algorithm_name]
            else:
                ''' Load the default parameters and add them to file '''
                d = get_default_algorithm_params(algorithm_name)
                with open(params_filename, 'r') as file:
                    params = json.load(file)
                params['algorithm'][algorithm_name] = d
                with open(params_filename, 'w') as file:
                    json.dump(params, file)
                return d
        except OSError:
            pass
    ''' If file does not exist, then load from introspection '''
    params = {'experiment': {}, 'algorithm': {'default': 'GridSearch'}}
    params['algorithm'][algorithm_name] = get_default_algorithm_params(algorithm_name)

    with open(params_filename, 'w') as file:
        json.dump(params, file)

    return params['algorithm'][algorithm_name]


def load_experiment_parameters(hub, experiment_name, default = False):
    ''' Looks for algorithm parameters in the parameterfile for the experiment. If none exist,
        get them from the default algorithm parameters and save a new parameterfile.

        Args:
            hub (Hub): a node whose experiment we're about to run
            experiment_name (str)
            default (bool)
    '''

    ''' Look for relevant parameters in the json file in the network's params directory '''
    params_filename = hub.network.params_path + '%s.%s.txt'%(hub.name, experiment_name)

    if not default:
        try:
            ''' Load params from file '''
            with open(params_filename, 'r') as file:
                params = json.load(file)

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
