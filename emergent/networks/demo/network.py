from emergent.networks.demo.hubs import DemoHub
from emergent.networks.demo.things import DemoThing
from emergent.networks.example import network as nw

def initialize(network, params = {}):
    ''' Initializes some Hubs and attached Things into the passed network. An
        optional params argument can overwrite default parameters by name; for
        example, if the network contains a Hub called 'hub' and a Thing called
        'thing', then passing {'hub': {'thing': {'devid': 137}}} will pass a
        params dict {'devid': 137} into the constructor for the 'thing' object.
        This is handled through the Network instance, which will be referenced by
        the Thing before setting its own params. Things can also be renamed from
        their default names through the 'name' field.
    '''
    network.add_params(params)          # add the passed params to the network

    hub = DemoHub('hub', network = network)

    thing = DemoThing('thing', params = {'inputs': ['Z']}, parent=hub)

    ''' Add hubs to network '''
    for hub in [hub]:
        network.add_hub(hub)

    ''' Load other network '''
    params = {'autoAlign': {'name': 'AA',
                            'params': {'MEMS':
                                        {'name': 'mems',
                                         'params': {'inputs': ['u', 'v']},
                                         'inputs': {'u': 'U', 'v': 'V'}
                                         }}}}

    nw.initialize(network, params = params)
