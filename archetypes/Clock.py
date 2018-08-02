import time
import numpy as np
from threading import Thread

class Clock():
    def __init__(self, parent):
        ''' Initializes the Clock and attaches it to a parent Control node '''
        self.parent = parent
        self.inputs = []
        self.state = {}

    def add_input(self, input):
        self.inputs.append(input)

    def start(self, T):
        states = self.prepare_sequence(T)
        self.loop_thread = Thread(target=self.loop)
        self.loop_thread.start()

        self.sync_thread = Thread(target=self.sync)
        self.sync_thread.start()

    def loop(self):
        ''' Loops through the specified sequence. The argument states is a list of tuples where the first element of each tuple is a delay and the second is a target state.'''
        i = 0
        while True:
            delay = self.sequence[i][0]
            state = self.sequence[i][1]
            time.sleep(delay)
            self.state = state
            i = (i+1)%len(self.sequence)

    def sync(self):
        ''' Keeps the physical state synced with another internal variable which can be set from another thread. This is useful for running sequences without additional delay due to actuation. '''
        while True:
            parent_substate = dict((k, self.parent.state[k]) for k in self.state.keys())
            if self.state != parent_substate:
                self.parent.actuate(self.state)

    def prepare_sequence(self, T):
        ''' Prepares a master sequence by combining sequences of all inputs '''
        times = []
        for input in self.inputs:
            times.extend([x[0]*T for x in input.sequence])
        times = np.unique(times)
        delays = np.append(np.array([0]),np.diff(times))
        states = []
        for i in range(len(times)):
            t = times[i]
            state = {}
            for input in self.inputs:
                input_times = [x[0]*T for x in input.sequence]
                current_index = np.where(input_times <= t)[0][-1]
                state[input.full_name] = input.sequence[current_index][1]
            states.append((delays[i], state))

        self.sequence = states
