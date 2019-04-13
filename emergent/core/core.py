import logging as log
import importlib
from emergent.utilities.networking import get_address
from emergent.core import ProcessHandler
from emergent.protocols.tick import TICKClient

class Core():
    ''' This class implements a container for multiple Hubs on a PC, as well as methods
        for getting or changing the state of Hubs on remote PCs.

        At runtime, main.py passes the Network object class into the EMERGENT network's
        initialize() method. For each local hub (Hub.addr matching the local address or
        unspecified), the Network adds the hub to its hubs dict.
    '''
    def __init__(self, name, addr=None, port=9001, database_addr=None):
        self.addr = addr
        if self.addr is None:
            self.addr = get_address()
        if database_addr is not None:
            self.database = TICKClient(database_addr, 'admin', 'admin', name)
            already_exists = False
            dbs = self.database.client.get_list_database()
            for db in dbs:
                if db['name'] == name:
                    already_exists = True
                    break
            if not already_exists:
                self.database.client.create_database(name)
        self.port = port
        self.name = name
        self.path = {'network': 'networks/%s'%name}
        self.path['data'] = self.path['network']+'/data/'
        self.path['state'] = self.path['network']+'/state/'
        self.path['params'] = self.path['network']+'/params/'
        self.path['sequences'] = self.path['network']+'/sequences/'
        self.path['pipelines'] = self.path['network']+'/pipelines/'

        self.tree = None
        self.connection_params = {'sync delay': 0.1, 'reconnect delay': 1}
        self.hubs = {}
        self.params = {}
        self.tasks = {}
        self.url = 'http://' + self.addr + ':' + str(self.port)
        self.manager = ProcessHandler()

    def __getstate__(self):
        ''' This method is called by the pickle module when attempting to serialize an
            instance of this class. We make sure to exclude any unpicklable objects from
            the return value, including anything with threads or Qt modules. '''
        d = {}
        ignore = ['manager', 'tree']
        unpickled = []
        for item in ignore:
            if hasattr(self, item):
                unpickled.append(getattr(self, item))
        for item in self.__dict__:
            if self.__dict__[item] not in unpickled:
                d[item] = self.__dict__[item]
        return d

    def actuate(self, state, send_over_p2p = True):
        ''' Issues a macroscopic actuation to all connected Hubs. '''
        for hub in state:
            self.hubs[hub].actuate(state[hub], send_over_p2p)

    def add_hub(self, hub):
        ''' If the address and port match self.addr and self.port, add a local
            hub. '''
        if hub.addr is not None:
            if not hub.addr == self.addr:
                return

        self.hubs[hub.name] = hub
        hub.core = self

    def add_params(self, params):
        ''' Add parameters passed in from the network's initialize() method
            to allow custom chunked networks to be constructed. '''
        for hub in params:
            if hub not in self.params:
                self.params[hub] = {}
            for thing in params[hub]:
                self.params[hub][thing] = params[hub][thing]

    def initialize(self):
        ''' Import the network.py file for the user-specified network and runs
            its initialize() method to instantiate all defined nodes. '''
        network_module = importlib.import_module('emergent.networks.'+self.name+'.network')
        network_module.initialize(self)

    def load(self):
        ''' Loads all attached Hub states from file. '''
        for hub in self.hubs.values():
            hub.load()

    def post_load(self):
        ''' Execute the post-load routine for all attached Hubs '''
        for hub in self.hubs.values():
            hub._on_load()

    def save(self):
        ''' Saves the state of all attached Hubs. '''
        for hub in self.hubs.values():
            hub.save()

    def set_range(self, settings):
        for hub_name in settings:
            hub = self.hubs[hub_name]
            for thing_name in settings[hub_name]:
                for knob_name in settings[hub_name][thing_name]:
                    d = settings[hub_name][thing_name][knob_name]
                    for qty in ['min', 'max']:
                        if qty in d:
                            hub.range[thing_name][knob_name][qty] = d[qty]

    def range(self):
        ''' Obtains a macroscopic range dict from aggregating the settings of all
            attached Hubs. '''
        settings = {}
        for hub in self.hubs.values():
            settings[hub.name] = hub.range

        return settings

    def state(self):
        ''' Obtains a macroscopic state dict from aggregating the states of all
            attached Hubs. '''
        state = {}
        for hub in self.hubs.values():
            state[hub.name] = hub.state

        return state


    def save_to_database(self):
        ''' Write the network state to the database. '''
        if hasattr(self, 'database'):
            self.database.write_network_state(self.state())

    def start_flask_socket_server(self):
        ''' Initialize Flask socket '''
        log.info('Starting socketIO client.')
        from socketIO_client import SocketIO, LoggingNamespace
        self.socketIO = SocketIO('localhost', 8000, LoggingNamespace)

    def emit(self, signal, arg=None):
        ''' Emit a signal over the SocketIO protocol. Using this method ensures
            that only allowed signals are emitted. '''
        signals = ['event',             # declare a new event in the TaskPanel; args: event dict
                   'timestep',          # update the current sequencer timestep; args: name
                   'sequencer',         # show sequencing grid
                   'sequence update',   # inform the GUI that the sequence has been updated
                   'actuate',           # broadcast a new state to the GUI; args: state dict (including hubs)
                   'sequence reorder',   # rearrange elements of a sequence,
                   'test',               # RPC for testing front-end events,
                   'plot',
                    ]
        assert signal in signals
        if hasattr(self, 'socketIO'):
            if arg is not None:
                self.socketIO.emit(signal, arg)
            else:
                self.socketIO.emit(signal)
        else:
            log.debug('Could not emit "%s": no socketIO client running.'%signal)

    def start_artiq_client(self):
        ''' Initialize Flask socket '''
        from socketIO_client import SocketIO, LoggingNamespace
        self.artiq_client = SocketIO('localhost', 54031, LoggingNamespace)
