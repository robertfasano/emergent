class MacroBuffer(list):
    def __init__(self, parent):
        super().__init__()
        self.length = 10
        self.index = -1
        self.parent = parent

    def add(self, state):
        if len(self) > 0:
            if state == self[-1]:
                return
            for i in range(self.index+1, 0):
                del self[i]
        self.append(state.copy())

        self.index = -1
        self.prune()

    def undo(self):
        if self.index-1 < -len(self):
            return
        last_state = self[self.index-1]
        if self.parent.node_type == 'knob':
            self.parent.parent.actuate({self.parent.name: last_state})
        elif self.parent.node_type == 'device':
            self.parent.parent.actuate({self.parent.name: last_state})
        elif self.parent.node_type == 'hub':
            self.parent.actuate(last_state)
        self.index -= 1
        self.prune()

    def redo(self):
        if self.index >= -1:
            return
        last_state = self[self.index+1]
        if self.parent.node_type == 'knob':
            self.parent.parent.actuate({self.parent.name: last_state})
        elif self.parent.node_type == 'device':
            self.parent.parent.actuate({self.parent.name: last_state})
        elif self.parent.node_type == 'hub':
            self.parent.actuate(last_state)
        self.index += 1
        self.prune()

    def prune(self):
        while len(self) > self.length:
            del self[0]

class StateBuffer(list):
    def __init__(self, parent):
        super().__init__()
        self.length = 10
        self.index = -1
        self.parent = parent

    def add(self, state):
        if len(self) > 0:
            if state == self[-1]:
                return
        for i in range(self.index+1, 0):
            del self[i]
        self.append(state.copy())

        self.index = -1
        self.prune()
    def undo(self):
        states = [self[i] for i in range(self.index, 0)]
        if self.index-1 < -len(self):
            return
        last_state = self[self.index-1]
        index = self.index
        self.index -= 1
        if self.parent.node_type == 'knob':
            self.parent.parent.actuate({self.parent.name: last_state})
        elif self.parent.node_type == 'device':
            self.parent.parent.actuate({self.parent.name: last_state})
        elif self.parent.node_type == 'hub':
            self.parent.actuate(last_state)
        del self[-1]        # don't add undo actuate to buffer
        self.extend(states)
        self.index = index - 1
        self.prune()

    def redo(self):
        states = [self[i] for i in range(self.index+1, 0)]
        if self.index >= -1:
            return
        last_state = self[self.index+1]
        index = self.index
        if self.parent.node_type == 'knob':
            self.parent.parent.actuate({self.parent.name: last_state})
        elif self.parent.node_type == 'device':
            self.parent.parent.actuate({self.parent.name: last_state})
        elif self.parent.node_type == 'hub':
            self.parent.actuate(last_state)
        del self[-1]        # don't add redo actuate to buffer
        self.index = index + 1
        self.extend(states)
        self.prune()

    def prune(self):
        while len(self) > self.length:
            del self[0]
