''' Parameter database class

    Usage: Call any of the API methods with a URI such as params?hub=hub&experiment=transmitted_power.
           Everything before the question mark is an endpoint, and everything after is the specific
           parameters needed by that endpoint. In the example URI above, calling ExperimentAPI.get() would
           parse the parameters into a dict and pass it into ExperimentAPI.params() to get the experimental
           parameters associated with a choice of experiment and/or model and/or sampler.

    When ExperimentAPI.get() is called, the ExperimentAPI first checks for an existing entry in its data
    attribute; if this is not found, it instead creates a default entry based on the default
    parameters of the experiment and/or model and/or sampler. Calling ExperimentAPI.save() will save
    to file, and it can be reloaded by calling ExperimentAPI.load(). '''

from emergent.utilities.recommender import get_default_params, get_default_experiment_params
import json
import collections

class ExperimentAPI():
    def __init__(self, network):
        ''' Args: network (str) '''
        self.path = 'networks/%s/params/experiment.json'%network.name
        self.data = {}
        self.network = network
        self.load()

    def load(self):
        try:
            with open(self.path, 'r') as file:
                self.data = json.load(file)
        except OSError:
            self.data = {}

    def save(self):
        with open(self.path, 'w') as file:
            json.dump(self.data, file)

    def get(self, string):
        ''' example_string = 'params?hub=hub&experiment=transmitted_power' '''
        endpoint = string.split('?')[0]
        params = string.split('?')[1]
        params_dict = {}

        if '=' in string:
            if '&' in string:
                params = params.split('&')
            for p in params:
                params_dict[p.split('=')[0]] = p.split('=')[1]
            return getattr(self, endpoint)(params_dict)
        else:
            return getattr(self, endpoint)()

    def params(self, params):
        hub = self.network.hubs[params['hub']]
        experiment = params['experiment']
        model = None
        if 'model' in params:
            model = params['model']
        sampler = None
        if 'sampler' in params:
            sampler = params['sampler']
        return {hub.name: {experiment: load_all_experiment_parameters(self, hub, experiment, model, sampler)}}

    def endpoint(self):
        return ['params']

    def patch_resource(self, old, new):
        ''' Updates any nested elements common to both dicts, but does NOT
            create new elements. '''
        for k, v in new.items():
            if isinstance(v, collections.Mapping):
                if k in old:
                    old[k] = self.patch_resource(old.get(k, {}), v)
            else:
                if k in old:
                    old[k] = v
        return old

    def put_resource(self, old, new):
        ''' Updates any nested elements common to both dicts, but does NOT
            create new elements. '''
        for k, v in new.items():
            if isinstance(v, collections.Mapping):
                old[k] = self.put_resource(old.get(k, {}), v)
            else:
                old[k] = v
        return old

    def patch(self, string, new_resource):
        ''' Recursively searches through the passed resource (generally a nested dict)
            and updates the stored dict with the most-nested values. Will not add new
            values or update higher levels. '''
        resource = self.get(string)
        resource = self.patch_resource(resource, new_resource)
        return resource

    def put(self, string, new_resource):
        ''' Recursively searches through the passed resource (generally a nested dict)
            and updates the stored dict with the most-nested values. Can add new
            values and/or update higher levels. '''
        resource = self.get(string)
        resource = self.put_resource(resource, new_resource)
        return resource


def load_all_experiment_parameters(database, hub, experiment_name, model_name=None, sampler_name=None):
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
        params = database.data[hub.name][experiment_name]

    except KeyError:
        ''' Entry doesn't yet exist; let's prepare a default file '''
        params = {'experiment': {}}
        if sampler_name is not None:
            params['sampler'] = {'default': sampler_name}
            params['sampler'][sampler_name] = get_default_params('sampler', sampler_name)
        if model_name is not None:
            params['model'] = {'default': model_name}
            params['model'][model_name] = get_default_params('model', model_name)

        params['experiment'] = get_default_experiment_params(hub, experiment_name)

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
    if hub.name not in database.data:
        database.data[hub.name] = {}
    database.data[hub.name][experiment_name] = params

    return p

if __name__ == '__main__':
    db = Database('example')
