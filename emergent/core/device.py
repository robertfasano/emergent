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
from emergent.protocols.serial import Serial
import socket
import serial

class Device():
    ''' Devices represent apparatus which can control the state of Knob
        nodes, such as a synthesizer or motorized actuator. '''

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        super().__init__(*args, **kwargs)
        instance.updatedict = {}
        return instance

    def __init__(self, name='', hub=None, params={}):
        """Initializes a Device.

        Args:
            name (str): node name. Devices which share a Hub should have unique names.
            hub (str): name of parent Hub.
        """
        self.simulation = False
        self.knobs = []
        self._name_ = name      # save hardcoded name as private variable
        self.params = params
        self.name = name
        self.options = {}
        self.buffer = StateBuffer(self)
        self.macro_buffer = MacroBuffer(self)
        self.hub = hub
        self.state = {}
        if self.hub is not None:
            hub.devices[name] = self
            self.hub.state[self.name] = self._state()
            self.hub.range[self.name] = {}
        self._connected = 0

        self.node_type = 'device'

        self.get_knobs()

        # self.__getstate__ = lambda: __getstate__(['hub', 'options'])

    def get_knobs(self):
        from emergent.core.knob import knob
        d = self.__class__.__dict__
        for item in d:
            if isinstance(d[item], knob):
                self.knobs.append(item)
                if self.hub is not None:
                    self.hub.state[self.name][item] = None
                    self.hub.range[self.name][item] = {'min': None, 'max': None}

    @abstractmethod
    def _actuate(self, state):
        for key in state:
            setattr(self, key, state[key])

    def _state(self):
        state = {}
        for prop in self.knobs:
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
            if self.hub is not None:
                self.hub.state[self.name][knob] = state[knob]   # update Hub



    def _open_tcpip(self, addr, port):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((addr, port))
        return client

    def _open_serial(self, port, baudrate=19200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1, encoding='ascii'):
        return Serial(
                port=port,
                baudrate=baudrate,
                parity=parity,
                stopbits=stopbits,
                bytesize=bytesize,
                timeout = timeout,
                encoding = encoding,
                name = self.name
            )

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((addr, port))
        return client
