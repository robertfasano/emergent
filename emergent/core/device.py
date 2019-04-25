'''
    A Device is some sort of actuator that can control the state of Knobs, like a
    DAC (for voltage generation) or a voltage driver for MEMS or motorized mirror
    mounts. The user must write a device driver script which implements the actuate()
    method to define the interface between EMERGENT and the manufacturer API. The Device
    class also contains methods for updating the macroscopic state representation
    after actuation and for adding or removing knobs dynamically.
'''
from abc import abstractmethod
from emergent.core import Node, Knob
from emergent.utilities.persistence import __getstate__
from emergent.utilities.buffers import StateBuffer, MacroBuffer

class Device():
    ''' Devices represent apparatus which can control the state of Knob
        nodes, such as a synthesizer or motorized actuator. '''

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        super().__init__(*args, **kwargs)
        instance.updatedict = {}
        return instance

    def __init__(self, name, hub, params={}):
        """Initializes a Device.

        Args:
            name (str): node name. Devices which share a Hub should have unique names.
            hub (str): name of parent Hub.
        """
        self.knobs = []
        self._name_ = name      # save hardcoded name as private variable
        self.params = params
        self.name = name
        self.options = {}
        self.buffer = StateBuffer(self)
        self.macro_buffer = MacroBuffer(self)
        self.hub = hub
        if self.hub is not None:
            hub.devices[name] = self
            self.hub.state[self.name] = self._state()
            self.hub.range[self.name] = {}
        # self.knobs = {}
        self._connected = 0
        # self.state = {}

        self.node_type = 'device'

        for p in self._properties():         # initialize knob
            getattr(self, p)
        self._add_boilerplate()
        # self.ignored = []       # objects to ignore during pickling

        # ''' Add knobs passed in params dict '''
        # if 'knobs' in self.params:
        #     for knob in self.params['knobs']:
        #         self.add_knob(knob)

        # self.__getstate__ = lambda: __getstate__(['hub', 'options'])

    # def add_knob(self, name):
    #     ''' Attaches a Knob node with the specified name. This should correspond
    #         to a specific name in the _actuate() function of a non-abstract Device
    #         class: for example, the PicoAmp MEMS driver has knobs explicitly named
    #         'X' and 'Y' which are referenced in PicoAmp._actuate().'''
    #     knob = Knob(name, device=self)
    #     self.knobs[name] = knob
    #     self.state[name] = None #self.knobs[name].state
    #
    #     if self.hub is not None:
    #         self.hub.state[self.name][name] = None
    #         self.hub.range[self.name][name] = {}
    #         for qty in ['min', 'max']:
    #             self.hub.range[self.name][name][qty] = None
    #         self.hub.core.emit('actuate', {self.hub.name: self.hub.state})
    #
    # def remove_knob(self, name):
    #     ''' Detaches the Knob node with the specified name. '''
    #     del self.knobs[name]
    #     del self.state[name]
    #     del self.hub.state[self.name][name]

    def _add_boilerplate(self):
        ''' Replaces each of the user-defined knob properties with a property implementing
            additional EMERGENT boilerplate code. '''
        def get_dict_attr(obj, attr):
            for obj in [obj] + obj.__class__.mro():
                if attr in obj.__dict__:
                    return obj.__dict__[attr]
            raise AttributeError

        def getter(self, name):
            ''' Calls the user-defined getter method with no changes. '''
            print('Adding boilerplate')
            return getattr(self, name)

        def setter(self, newval, name):
            ''' Calls the user-defined setter method, then updates the hub state dict. '''
            print('setting', name)
            setattr(self, name, newval)        # call user-defined setter method
            # setattr(self, name[1::], newval)   # update private variable in case user forgets
            #
            # if self.hub is not None:
            #     self.hub.state[self.name][name.split('_')[1]] = newval

        for prop in self.knobs:
            new = '__%s'%prop
            # setattr(self.__class__, new, get_dict_attr(self, prop))
            print('Add boilerplate to', prop)
            setattr(self.__class__, prop, property(lambda self, name=new: getter(self, name),
                                                   lambda self, newval, name=new: setter(self, newval, name)))

    @abstractmethod
    def _actuate(self, state):
        for key in state:
            setattr(self, key, state[key])

    def _properties(self):
        return [p for p in self.__class__.__dict__ if isinstance(getattr(self.__class__,p),property)]

    def _state(self):
        state = {}
        for prop in self._properties():
            if '__' not in prop:
                state[prop] = getattr(self, prop)
        return state

    @abstractmethod
    def _connect(self):
        """Private placeholder for the device-specific initiation method. """
        return 1

    def actuate(self, state, send_over_p2p = True):
        """Makes a physical device change in the lab with the _actuate() method, then registers this change with EMERGENT.

        Args:
            state (dict): Target state of the form {'param1':value1, 'param2':value2,...}.
        """
        state = state.copy()
        for key in list(state.keys()):
            if state[key] is None:
                del state[key]
        self._actuate(state)


        ''' Update the state of the Knob, Device, and Hub '''
        for knob in state:
            # self.state[knob] = state[knob]    # update Device
            if self.hub is not None:
                self.hub.state[self.name][knob] = state[knob]   # update Hub

            ''' update state buffer '''
            # self.knobs[knob].buffer.add(state)
        # self.buffer.add(self.state)
