'''
    A Thing is some sort of actuator that can control the state of Knobs, like a
    DAC (for voltage generation) or a voltage driver for MEMS or motorized mirror
    mounts. The user must write a device driver script which implements the actuate()
    method to define the interface between EMERGENT and the manufacturer API. The Thing
    class also contains methods for updating the macroscopic state representation
    after actuation and for adding or removing knobs dynamically.
'''
from abc import abstractmethod
from emergent.core import Node, Knob
from emergent.utilities.persistence import __getstate__

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

        super().__init__(name, parent=parent)
        self._connected = 0
        self.state = {}

        self.parent.state[self.name] = {}
        self.parent.range[self.name] = {}

        self.node_type = 'thing'
        self.ignored = []       # objects to ignore during pickling

        ''' Add knobs passed in params dict '''
        if 'knobs' in self.params:
            for knob in self.params['knobs']:
                self.add_knob(knob)

        self.__getstate__ = lambda: __getstate__(['parent', 'options'])

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

    def actuate(self, state, send_over_p2p = True):
        """Makes a physical thing change in the lab with the _actuate() method, then registers this change with EMERGENT.

        Args:
            state (dict): Target state of the form {'param1':value1, 'param2':value2,...}.
        """
        state = state.copy()
        for key in list(state.keys()):
            if state[key] is None:
                del state[key]
        self._actuate(state)


        ''' Update the state of the Knob, Thing, and Hub '''
        for knob in state:
            self.state[knob] = state[knob]    # update Thing
            self.children[knob].state = state[knob]   # update Knob
            self.parent.state[self.name][knob] = state[knob]   # update Hub

            ''' update state buffer '''
            self.children[knob].buffer.add(state)
        self.buffer.add(self.state)

        if send_over_p2p:
            self.parent.core.emit('actuate', {self.parent.name: {self.name: state}})
