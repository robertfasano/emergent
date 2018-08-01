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
        self.loop_thread = Thread(target=self.loop,args=(states))
        self.loop_thread.start()
        
        self.sync_thread = Thread(target=self.sync)
        self.sync_thread.start()
        
    def loop(self, states):
        ''' Loops through the specified sequence. The argument states is a list of tuples where the first element of each tuple is a delay and the second is a target state.'''
        i = 0
        while True:
            delay = states[i][0]
            state = states[i][1]
            time.sleep(delay)
            self.state = state
            i = (i+1)%len(states)
            
    def sync(self):
        ''' Keeps the physical state synced with another internal variable which can be set from another thread. This is useful for running sequences without additional delay due to actuation. '''
        while True:
            if self.state != self.parent.state:
                self.parent.actuate(self.state)
                
    def prepare_sequence(self, T):
        ''' Prepares a master sequence by combining sequences of all inputs '''
        times = []
        for input in self.inputs:
            times.extend([x[0]*T for x in input.sequence)
        times = np.unique(times)
        
        states = []
        for t in times:
            state = {}
            for input in self.inputs:
                input_times = [x[0]*T for x in input.sequence]
                current_index = np.where(input_times <= time)[-1]
                state[input.name] = input.sequence[current_index]
            states.append((t, state))
            
        ''' Convert times to delays '''
        states[0][0] = 0
        for i in range(1,len(states)):
            states[i][0] = states[i][0]-states[i-1][0]
        return states

            
    