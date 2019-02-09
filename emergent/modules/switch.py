class Switch():
    def __init__(self, name, params, invert = False):
        self.name = name
        self.params = params
        self.state = None
        self.invert = invert

        self.set(0)

    def set(self, state):
        if self.invert:
            state = 1-state
        if state == self.state:         # ignore commands that would leave the state unchanged
            return
        self._set(state)
        self.state = state

    def _set(self, state):
        ''' Overload with device-specific switching command '''
        print(self.name, state)

    def toggle(self):
        if self.invert:
            state = self.state
        else:
            state = 1-self.state
        self.set(state)
