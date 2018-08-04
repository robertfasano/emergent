import time
import numpy as np
from threading import Thread
from archetypes.parallel import ProcessHandler

class Clock(ProcessHandler):
    ''' The Clock class attaches to a Control node to provide sequencing capabilities:
        waveforms can be specified for any connected Input nodes, and the Clock
        combines all input sequences into a master sequence describing the
        state of all sequenced Input nodes at each point during the experimental
        cycle. '''
    def __init__(self, parent):
        ''' Initializes the Clock and attaches it to a parent Control node '''
        ProcessHandler.__init__(self)
        self.parent = parent
        self.inputs = []
        self.state = {}

    def add_input(self, input):
        ''' Connects an Input node to the Clock, allowing sequencing. '''
        self.inputs.append(input)

    def start(self, T):
        ''' Prepares and runs the master sequence. To reduce timing jitter,
        two threads are used: one which updates the internal Clock state at all times
        (very computationally quick) and another which actuates the Control node
        to keep in sync with the Clock state (more time-intensive).'''
        states = self.prepare_sequence(T)
        self._run_thread(self.loop)
        self._run_thread(self.sync)

    def stop(self):
        ''' Terminates sequencing. '''
        self._quit_thread(self.loop)
        self._quit_thread(self.sync)

    def loop(self, stopped):
        ''' Loops through the specified sequence. The argument states is a list
        of tuples where the first element of each tuple is a delay and the second
        is a target state.'''
        i = 0
        while not stopped():
            delay = self.sequence[i][0]
            state = self.sequence[i][1]
            time.sleep(delay)
            self.state = state
            i = (i+1)%len(self.sequence)

    def sync(self, stopped):
        ''' Keeps the Control state synced with the Clock state.  '''
        while not stopped():
            parent_substate = dict((k, self.parent.state[k]) for k in self.state.keys())
            if self.state != parent_substate:
                self.parent.actuate(self.state)

    def prepare_sequence(self, T):
        ''' Prepares a master sequence by combining sequences of all inputs. '''
        times = []
        for input in self.inputs:
            times.extend([x[0]*T for x in input.sequence])
        times = np.unique(times)

        delays = np.append(np.array([T-np.sum(np.diff(times))]),np.diff(times))
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
