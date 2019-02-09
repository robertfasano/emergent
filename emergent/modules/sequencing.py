''' This module allows definition and generation of TTL patterns. It also offers
    convenient options to control the TTL state through the GUI - every timestep
    added to the Sequencer appears as an input whose duration can be altered, and
    a specific state can be set by right-clicking on the input. '''
import time
import logging as log
import pandas as pd
import numpy as np
from emergent.modules import Thing

class Timestep():
    ''' A container for state representation of many switches at a given time. '''
    def __init__(self, name, duration, state):
        ''' Args:
                name (str): the name of this timestep
                duration (float): the duration of this timestep in seconds
                state (dict): boolean state of all switches at this timestep
        '''
        self.name = name
        self.duration = duration
        self.state = state

class Sequencer(Thing):
    ''' This class handles TTL pattern generation in a way that is easy
        to define, device-agnostic, and easily testable in the lab. '''
    def __init__(self, name, parent, params={'steps': [], 'labjack': None}):
        Thing.__init__(self, name, parent, params=params)
        self.channels = []
        self.labjack = params['labjack']
        goto_option = lambda s: lambda: self.goto(s)

        for step in params['steps']:
            self.add_input(step.name)
            self.children[step.name].options = {'Go to %s'%step.name: (goto_option(step.name))}
            for channel in step.state:
                if channel not in self.channels:
                    self.channels.append(channel)

        self.steps = params['steps']
        self.cycle_time = 0

    def get_time(self, step):
        ''' Returns the time when the specified integer step starts '''
        now = 0
        for i in range(step):
            now += self.state[self.steps[i].name]
        return now

    def goto(self, step):
        ''' Go to a step specified by an integer or string name. '''
        step = self.get_step(step)
        for channel in step.state:
            self.parent.switches[channel].set(step.state[channel])

    def get_step(self, step):
        ''' Returns a Timestep object corresponding to the passed integer (place)
            or string (name). '''
        if isinstance(step, int):
            return self.steps[step]
        elif isinstance(step, str):
            for s in self.steps:
                if s.name == step:
                    return s
        else:
            log.warning('Invalid timestep specified.')
            return -1

    def form_stream(self, dt=1e-4):
        ''' Prepare a dataframe representing the streamed switch states '''
        self.cycle_time = 0
        for s in self.steps:
            self.cycle_time += self.state[s.name]
        stream_steps = int(self.cycle_time/dt)

        t = np.linspace(0, self.cycle_time, stream_steps)
        stream = pd.DataFrame(index=t, columns=self.channels)
        now = 0
        for step in self.steps:
            duration = self.state[step.name]
            timeslice = stream.index[(stream.index >= now) & (stream.index <= now + duration)]
            for channel in step.state:
                stream.loc[timeslice, channel] = step.state[channel]
            now += duration

        return stream

    def prepare(self):
        ''' Parse the sequence into the proper form to send to the LabJack.
            Returns:
                numpy.ndarray: an array of bitmasks corresponding to the overall
                               state at each timestep. '''

        ''' Get channel numbers and prepare digital stream '''
        channel_numbers = []
        for channel in self.channels:
            channel_numbers.append(self.parent.switches[channel].channel)
        self.labjack.prepare_digital_stream(channel_numbers)
        self.labjack.prepare_stream_out(trigger=0)
        stream = self.form_stream()
        bitmask = self.labjack.array_to_bitmask(stream.values, channel_numbers)
        sequence, scan_rate = self.labjack.resample(np.atleast_2d(bitmask).T, self.cycle_time)
        self.labjack.stream_out(['FIO_STATE'], sequence, scan_rate, loop=0)

    def run(self):
        ''' Run the sequence non-deterministically. '''
        while True:
            loop_start_time = time.time()
            while True:
                t = time.time() - loop_start_time
                if t > self.cycle_time:
                    break
                ''' Get step corresponding to current time and set it '''
                current_step = 0
                for i in range(len(self.steps)):
                    step_start_time = self.get_time(i)
                    if step_start_time < t:
                        current_step = i
                self.goto(current_step)

    def run_labjack(self):
        self.prepare()
        if self.labjack.stream_mode != 'in-triggered':
            self.labjack.prepare_streamburst(0, trigger=0)
        self.parent.stream_complete = False
        data = np.array(self.labjack.streamburst(self.cycle_time))
        self.parent.stream_complete = True

        return data
