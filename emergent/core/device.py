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

class Device(Node):
    ''' Devices represent apparatus which can control the state of Knob
        nodes, such as a synthesizer or motorized actuator. '''

    def __init__(self, name, hub, params={}):
        """Initializes a Device.

        Args:
            name (str): node name. Devices which share a Hub should have unique names.
            hub (str): name of parent Hub.
        """
        self._name_ = name      # save hardcoded name as private variable
        self.params = params

        super().__init__(name)
        hub.devices[name] = self
        self.hub = hub

        self.knobs = {}
        self._connected = 0
        self.state = {}

        self.hub.state[self.name] = {}
        self.hub.range[self.name] = {}

        self.node_type = 'device'
        self.ignored = []       # objects to ignore during pickling

        ''' Add knobs passed in params dict '''
        if 'knobs' in self.params:
            for knob in self.params['knobs']:
                self.add_knob(knob)

        self.__getstate__ = lambda: __getstate__(['hub', 'options'])

    def add_knob(self, name):
        ''' Attaches a Knob node with the specified name. This should correspond
            to a specific name in the _actuate() function of a non-abstract Device
            class: for example, the PicoAmp MEMS driver has knobs explicitly named
            'X' and 'Y' which are referenced in PicoAmp._actuate().'''
        knob = Knob(name, device=self)
        self.knobs[name] = knob
        self.state[name] = None #self.knobs[name].state
        self.hub.state[self.name][name] = None
        self.hub.range[self.name][name] = {}
        for qty in ['min', 'max']:
            self.hub.range[self.name][name][qty] = None
        self.hub.core.emit('actuate', {self.hub.name: self.hub.state})

    def remove_knob(self, name):
        ''' Detaches the Knob node with the specified name. '''
        del self.knobs[name]
        del self.state[name]
        del self.hub.state[self.name][name]

    @abstractmethod
    def _actuate(self, state):
        """Private placeholder for the device-specific driver.

        Note:
            State actuation is done by first calling the Device.actuate() method,
            which calls Device._actuate(state) to change something in the lab, then
            calls Device.update(state) to register this new state with EMERGENT.
            When you write a driver inheriting from Device, you should reimplement
            this method to update your device to the specified state only - do not
            update any stored states such as Device.state, Knob.state, or Hub.state
            from this method.

        Args:
            state (dict): Target state such as {'param1':value1, 'param2':value2}.
        """
        return

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
            self.state[knob] = state[knob]    # update Device
            # self.knobs[knob].state = state[knob]   # update Knob
            self.hub.state[self.name][knob] = state[knob]   # update Hub

            ''' update state buffer '''
            self.knobs[knob].buffer.add(state)
        self.buffer.add(self.state)
