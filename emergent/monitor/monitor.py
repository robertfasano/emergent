import json
import datetime
from functools import partial
from emergent.utilities.decorators import thread
import time
import logging as log
log.basicConfig(level=log.INFO)
import sched

class Monitor():
    def __init__(self, watchdogs = {}, filename = None):
        self.watchdogs = watchdogs
        self.filename = filename
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.trigger = None

    def add(self, key, watchdog):
        self.watchdogs[key] = watchdog

    def check(self):
        state = {'time': datetime.datetime.now().isoformat(),
                 'values': {},
                 'states': {}}
        for w in self.watchdogs:
            value, tf = self.watchdogs[w].check()
            state['values'][w] = value
            state['states'][w] = int(tf)

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
    def start_triggered(self, trigger=None):
        if trigger is None:
            trigger = self.trigger
        self.on = 1

        if trigger is None:
            log.warn('Attach or pass a trigger!')
            return

        while self.on:
            trigger()
            self.check()

    @thread
    def start_periodic(self, period):
        self.on = 1
        if not hasattr(self, 'last_time'):
            self.last_time = time.time()
        while self.on:
            self.scheduler.enterabs(self.last_time, 1, self.check)
            self.last_time += period
            self.scheduler.run()


    def stop(self):
        self.on = 0
