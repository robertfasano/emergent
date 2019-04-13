import json
import datetime

class Monitor():
    def __init__(self, watchdogs = {}, filename = None):
        self.watchdogs = watchdogs
        self.filename = filename

    def add(self, key, watchdog):
        self.watchdogs[key] = watchdog

    def check(self):
        state = {'time': datetime.datetime.now().isoformat(),
                 'values': {},
                 'states': {}}
        for w in self.watchdogs:
            value, tf = self.watchdogs[w].check()
            state['values'][w] = value
            state['states'][w] = tf

        if self.filename is not None:
            self.log(state, self.filename)

        return state

    def log(self, state, filename):
        ''' Append a timestamped state dict to a file. '''
        with open(filename, 'a') as file:
            file.write(json.dumps(state)+'\n')
