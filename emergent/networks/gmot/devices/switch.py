''' This module implements logical switches, which can be used to control either
    virtual flags or physical TTL lines. '''
class Switch():
    ''' A generic switch with on/off states and methods to set or toggle the
        state. The user should overload the _set method when inheriting this
        class in order to switch an actual device. '''
    def __init__(self, name, params, invert=False, channel=None):
        self.name = name
        self.params = params
        self.state = None
        self.invert = invert
        self.channel = channel

        self.set(0)

    def set(self, state):
        ''' Set the state of the switch. If self.invert, the physical state will
            be the opposite of the virtual state - this is offered for convenience
            when switch states are unintuitive, e.g. when TTL low turns a device on. '''
        self.state = state
        if self.invert:
            state = 1-state
        # if state == self.state:         # ignore commands that would leave the state unchanged
        #     return
        self._set(state)

    def _set(self, state):
        ''' Overload with device-specific switching command '''
        print(self.name, state)

    def toggle(self):
        ''' Toggles the switch state. '''
        if self.invert:
            state = self.state
        else:
            state = 1-self.state
        self.set(state)

class LabJackSwitch(Switch):
    def __init__(self, name, params, invert = False):
        self.labjack = params['labjack']
        self.channel = params['channel']
        super().__init__(name, params, invert = invert, channel = self.channel)

    def _set(self, state):
        ''' Overload with device-specific switching command, e.g. LabJack as shown '''
        self.labjack.DOut(self.channel, state)
