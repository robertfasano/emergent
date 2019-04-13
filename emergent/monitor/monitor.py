import json
import datetime
from functools import partial
from emergent.utilities.decorators import thread
import time
import logging as log
log.basicConfig(level=log.INFO)

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

    def wait_trigger(self, period):
        time.sleep(period)

    @thread
    def start(self, period=None):
        self.on = 1
        if period is not None:
            self.trigger = partial(self.wait_trigger, period)
        if not hasattr(self, 'trigger'):
            log.warn('Attach a trigger or define a period!')
            return
        while self.on:
            self.trigger()
            self.check()

    def stop(self):
        self.on = 0
