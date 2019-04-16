''' Implements the Node class, which contains methods for relating EMERGENT building
    blocks to one another. Three further classes inherit from Node: the Knob, Thing,
    and Hub.

    A Knob represents a physical quantity that you can set in the lab, like a
    voltage or a mirror position. The Knob class simply tracks a value for a
    "knob" in your experiment.

    A Thing is some sort of actuator that can control the state of Knobs, like a
    DAC (for voltage generation) or a voltage driver for MEMS or motorized mirror
    mounts. The user must write a device driver script which implements the actuate()
    method to define the interface between EMERGENT and the manufacturer API. The Thing
    class also contains methods for updating the macroscopic state representation
    after actuation and for adding or removing knobs dynamically.

    A Hub is an object which controls one or more Things to regulate the outcome
    of an experiment. For example, for beam alignment into an optical fiber we would
    require one or more Things for mirror control, as well as a Hub which measures
    the transmitted power and coordinates commands to its connected Things to maximize
    the signal. The Hub class also contains methods for saving and loading states
    to/from file, for monitoring important variables through the Watchdog framework,
    and for optimizing itself by interfacing with other modules.
'''
from abc import abstractmethod
from emergent.core import Node, Knob

class Thing(Node):
    ''' Things represent apparatus which can control the state of Knob
        nodes, such as a synthesizer or motorized actuator. '''

    def __init__(self, name, parent, params={}):
        """Initializes a Thing.

        Args:
            name (str): node name. Things which share a Hub should have unique names.
            parent (str): name of parent Hub.
        """
        self._name_ = name      # save hardcoded name as private variable
        self.local = True
        if not parent.local:
            self.local = False
            return
        self.params = params
        ''' Update self.params with any parameters associated with the Network '''
        try:
            core_params = parent.core.params[parent._name_]['params'][name]['params']
        except KeyError:
            core_params = {}
        for p in core_params:
            self.params[p] = core_params[p]
        if 'name' in self.params:
            name = self.params['name']


        # ''' Rename from hub dictionary '''
        # if name in parent.renaming:
        #     name = parent.renaming[name]['name']

        super().__init__(name, parent=parent)
        self._connected = 0
        self.state = {}
        # self.state = State()

        self.parent.state[self.name] = {}
        self.parent.range[self.name] = {}

        self.loaded = 0     # set to 1 after first state preparation
        self.node_type = 'thing'
        self.ignored = []       # objects to ignore during pickling

        ''' Add knobs passed in params dict '''
        if 'knobs' in self.params:
            for knob in self.params['knobs']:
                self.add_knob(knob)

    def __getstate__(self):
        ''' When the pickle module attempts to serialize this node to file, it
            calls this method to obtain a dict to serialize. We intentionally omit
            any unpicklable objects from this dict to avoid errors. '''
        d = {}
        ignore = ['parent', 'root', 'leaf', 'options']
        ignore.extend(self.ignored)
        unpickled = []
        for item in ignore:
            if hasattr(self, item):
                unpickled.append(item)

        for item in self.__dict__:
            obj = getattr(self, item)
            if hasattr(obj, 'picklable'):
                if not obj.picklable:
                    continue
            if item not in unpickled:
                d[item] = self.__dict__[item]
        return d

    def add_knob(self, name):
        ''' Attaches a Knob node with the specified name. This should correspond
            to a specific name in the _actuate() function of a non-abstract Thing
            class: for example, the PicoAmp MEMS driver has knobs explicitly named
            'X' and 'Y' which are referenced in PicoAmp._actuate().'''
        knob = Knob(name, parent=self)
        self.children[name] = knob
        self.state[name] = self.children[name].state
        self.parent.state[self.name][name] = None
        self.parent.range[self.name][name] = {}
        for qty in ['min', 'max']:
            self.parent.range[self.name][name][qty] = None
        self.parent.core.emit('actuate', {self.parent.name: self.parent.state})
        #if self.loaded:
            # self.actuate({name:self.parent.state[self.name][name]})
            #log.warning('Knobs changed but not actuated; physical state not synced with virtual state. Run parent.actuate(parent.state) to resolve, where parent is the name of the parent hub node.')

    def remove_knob(self, name):
        ''' Detaches the Knob node with the specified name. '''
        del self.children[name]
        del self.state[name]
        del self.parent.state[self.name][name]

    @abstractmethod
    def _actuate(self, state):
        """Private placeholder for the thing-specific driver.

        Note:
            State actuation is done by first calling the Thing.actuate() method,
            which calls Thing._actuate(state) to change something in the lab, then
            calls Thing.update(state) to register this new state with EMERGENT.
            When you write a driver inheriting from Thing, you should reimplement
            this method to update your thing to the specified state only - do not
            update any stored states such as Thing.state, Knob.state, or Hub.state
            from this method.

        Args:
            state (dict): Target state such as {'param1':value1, 'param2':value2}.
        """
        return

    @abstractmethod
    def _connect(self):
        """Private placeholder for the thing-specific initiation method. """
        return 1

    def _translate(self, state):
        ''' Convert a state with display names into a state with original names. '''
        new_state = {}
        for display_name in state:
            for node in self.children.values():
                if node.display_name == display_name:
                    new_state[node.name] = state[display_name]

        return new_state

    def actuate(self, state, send_over_p2p = True):
        """Makes a physical thing change in the lab with the _actuate() method, then registers this change with EMERGENT.

        Args:
            state (dict): Target state of the form {'param1':value1, 'param2':value2,...}.
        """
        ''' Translate to original knob names to send to driver '''
        # print(state)
        # for knob_name in state:
        #     knob = self.children[knob_name]
        #     if knob_name != knob._name_:
        #         state[knob._name_] = state.pop(knob.name)
        # print(state)
        state = state.copy()
        for key in list(state.keys()):
            if state[key] is None:
                del state[key]
        translated_state = self._translate(state)
        self._actuate(translated_state)
        self.update(state)

        if send_over_p2p:
            self.parent.core.emit('actuate', {self.parent.name: {self.name: state}})

    def update(self, state):
        """Synchronously updates the state of the Knob, Thing, and Hub.

        Args:
            state (dict): New state, e.g. {'param1':value1, 'param2':value2}.
        """
        for knob in state:
            self.state[knob] = state[knob]    # update Thing
            self.children[knob].state = state[knob]   # update Knob
            self.parent.state[self.name][knob] = state[knob]   # update Hub

            ''' update state buffer '''
            self.children[knob].buffer.add(state)
        self.buffer.add(self.state)
