''' This module allows definition and generation of TTL patterns. It also offers
    convenient options to control the TTL state through the GUI - every timestep
    added to the Sequencer appears as a knob whose duration can be altered, and
    a specific state can be set by right-clicking on the knob. '''
import time
import logging as log
import pandas as pd
import numpy as np
import json
from emergent.core import Device

class Sequence():
    ''' A container for a sequence of one or more Timesteps. '''
    def __init__(self, name, steps):
        self.name = name
        self.steps = steps

class Sequencer(Device):
    ''' This class handles TTL pattern generation in a way that is easy
        to define, device-agnostic, and easily testable in the lab. '''

    def __init__(self, name, hub, params={'sequence': {}, 'labjack': None}):
        Device.__init__(self, name, hub, params=params)
        if 'labjack' in params:
            self.labjack = params['labjack']
        self.options['Show grid'] = self.open_grid
        # self.options['Save'] = self.save
        # self.options['Load'] = self.load

        goto_option = lambda s: lambda: self.goto(s)
        move_down_option = lambda s: lambda: self.move(s, 1)
        move_up_option = lambda s: lambda: self.move(s, -1)

        self.ttl = []
        self.adc = []
        self.dac = []
        for step in params['sequence']:
            self.add_knob(step['name'])
            self.knobs[step['name']].options = {'Go to %s'%step['name']: (goto_option(step['name']))}

            for ch in step['TTL']:
                if ch not in self.ttl:
                    self.ttl.append(ch)
            for ch in step['ADC']:
                if ch not in self.adc:
                    self.adc.append(ch)
            for ch in step['DAC']:
                if ch not in self.dac:
                    self.dac.append(ch)

        self.steps = params['sequence']
        self.cycle_time = 0
        self.current_step = None

    def _actuate(self, state):
        for step in state:
            s = self.get_step_by_name(step)
            s['duration'] = state[step]

    def get_switch_by_channel(self, ch):
        for switch in self.hub.switches.values():
            if switch.channel == ch:
                return switch

    def get_step_by_name(self, name):
        for step in self.steps:
            if step['name'] == name:
                return step

    def get_time(self, step):
        ''' Returns the time when the specified integer step starts '''
        now = 0
        for step in self.steps:
            now += self.state[step['name']]
        return now

    def goto(self, step_name):
        ''' Go to a step specified by a string name. '''
        step = self.get_step_by_name(step_name)
        for switch in self.hub.switches.values():
            if int(switch.channel) in step['TTL'] or str(switch.channel) in step['TTL']:
                switch.set(1)
            else:
                switch.set(0)

        self.current_step = step_name
        if hasattr(self, 'grid'):
            self.grid.bold_active_step()

    # def get_step(self, step):
    #     ''' Returns a Timestep object corresponding to the passed integer (place)
    #         or string (name). '''
    #     if isinstance(step, int):
    #         return self.steps[step]
    #     elif isinstance(step, str):
    #         for s in self.steps:
    #             if s.name == step:
    #                 return s
    #     else:
    #         log.warning('Invalid timestep specified.')
    #         return -1

    # def add_step(self, name, duration = 0):
    #     ''' Creates a new step with default TTL off state. '''
    #     state = {}
    #     for switch in self.hub.switches:
    #         state[switch] = 0
    #     step = Timestep(name, duration, state)
    #     self.steps.append(step)
    #
    #     goto_option = lambda s: lambda: self.goto(s)
    #     move_down_option = lambda s: lambda: self.move(s, 1)
    #     move_up_option = lambda s: lambda: self.move(s, -1)
    #     self.add_knob(step)
    #     self.knobs[step].options = {'Go to %s'%step: (goto_option(step))}
    #     self.knobs[step].options['Move up'] = move_up_option(step)
    #     self.knobs[step].options['Move down'] = move_down_option(step)
    #     self.hub.actuate({'sequencer': {step: 0}})
    #
    #     ''' Redraw grid '''
    #     if hasattr(self, 'grid'):
    #         self.grid.redraw()

    # def remove_step(self, name):
    #     ''' Removes a step '''
    #
    #     ''' Remove from class list '''
    #     i = 0
    #     for step in self.steps:
    #         if step == name:
    #             del self.steps[i]
    #             break
    #         i += 1
    #
    #     ''' Remove from knobs '''
    #     self.remove_knob(name)
    #
    #     ''' Redraw grid '''
    #     if hasattr(self, 'grid'):
    #         self.grid.redraw()

    # def _rename_knob(self, node, name):
    #     for step in self.steps:
    #         if step == node.name:
    #             step = name
    #     if hasattr(self, 'grid'):
    #         self.grid.redraw()

    # def move(self, step, n):
    #     ''' Moves the passed step (integer or string) n places to the left (negative n)
    #         or right (positive n). '''
    #     step = self.get_step(step)
    #     ''' get integer place '''
    #     i = 0
    #     for s in self.steps:
    #         if s.name == step:
    #             break
    #         i += 1
    #     self.steps.insert(i+n, self.steps.pop(i))
    #
    #     ''' Move in NetworkPanel '''
    #     knob_node = self.knobs[step]
    #     knob_node.leaf.move(n)
    #
    #     ''' Redraw grid '''
    #     if hasattr(self, 'grid'):
    #         self.grid.redraw()


    def form_stream(self, dt=1e-4):
        ''' Prepare a dataframe representing the streamed switch states '''
        self.cycle_time = 0
        for s in self.steps:
            self.cycle_time += self.state[s['name']]/1000
        stream_steps = int(self.cycle_time/dt)

        t = np.linspace(0, self.cycle_time, stream_steps)
        stream = pd.DataFrame(index=t, columns=self.ttl)
        now = 0
        for step in self.steps:
            duration = self.state[step['name']]/1000
            timeslice = stream.index[(stream.index >= now) & (stream.index <= now + duration)]
            for channel in step['TTL']:
                state = step['TTL'][channel]         # add invert
                if self.hub.switches[channel].invert:
                    state = 1-state
                stream.loc[timeslice, channel] = state          # use the physical state, not the virtual, possibly inverted, state
            now += duration

        return stream

    def open_grid(self):
        self.hub.core.emit('sequencer', {'hub': self.hub.name})

    def prepare(self):
        ''' Parse the sequence into the proper form to send to the LabJack.
            Returns:
                numpy.ndarray: an array of bitmasks corresponding to the overall
                               state at each timestep. '''

        ''' Get channel numbers and prepare digital stream '''
        channel_numbers = []
        for channel in self.ttl:
            channel_numbers.append(self.hub.switches[channel].channel)
        self.labjack.prepare_digital_stream(channel_numbers)
        self.labjack.prepare_stream_out(trigger=0)
        stream = self.form_stream()
        bitmask = self.labjack.array_to_bitmask(stream.values, channel_numbers)
        sequence, scan_rate = self.labjack.resample(np.atleast_2d(bitmask).T, self.cycle_time)
        self.labjack.stream_out(['FIO_STATE'], sequence, scan_rate, loop=0)

    # def prepare_io(self):
    #     ''' Parse the sequence into the proper form to send to the LabJack.
    #         Returns:
    #             numpy.ndarray: an array of bitmasks corresponding to the overall
    #                            state at each timestep. '''
    #
    #     ''' Get channel numbers and prepare digital stream '''
    #     channel_numbers = []
    #     for channel in self.ttl:
    #         channel_numbers.append(self.hub.switches[channel].channel)
    #     self.labjack.prepare_digital_stream(channel_numbers)
    #     self.labjack.prepare_stream_out(trigger=0)
    #     stream = self.form_stream()
    #     bitmask = self.labjack.array_to_bitmask(stream.values, channel_numbers)
    #     sequence, scan_rate = self.labjack.resample(np.atleast_2d(bitmask).T, self.cycle_time)
    #     self.labjack.stream_out(['FIO_STATE'], sequence, scan_rate, loop=0)

    # def run(self):
    #     ''' Run the sequence non-deterministically. '''
    #     while True:
    #         loop_start_time = time.time()
    #         while True:
    #             t = time.time() - loop_start_time
    #             if t > self.cycle_time:
    #                 break
    #             ''' Get step corresponding to current time and set it '''
    #             current_step = 0
    #             for i in range(len(self.steps)):
    #                 step_start_time = self.get_time(i)
    #                 if step_start_time < t:
    #                     current_step = i
    #             self.goto(current_step)

    # def run_labjack(self):
    #     self.prepare()
    #     if self.labjack.stream_mode != 'in-triggered':
    #         self.labjack.prepare_streamburst(0, trigger=0)
    #     self.hub.stream_complete = False
    #     data = np.array(self.labjack.streamburst(self.cycle_time))
    #     self.hub.stream_complete = True
    #     self.current_step = self.steps[-1].name
    #
    #     return data

    # def save(self):
    #     filename = self.hub.core.path['state'] + 'sequence.json'
    #     sequence = {}
    #     for step in self.steps:
    #         sequence[step] = {'duration': self.state[step],
    #                                'state': step['state']}
    #     with open(filename, 'w') as file:
    #         json.dump(sequence, file)

    # def load(self):
    #     filename = self.hub.core.path['state'] + 'sequence.json'
    #     with open(filename, 'r') as file:
    #         sequence = json.load(file)
    #
    #     self.steps = []
    #     knobs = list(self.knobs.keys())
    #     state = {}
    #     for knob in knobs:
    #         self.remove_knob(knob)
    #     for step in sequence:
    #         s = Timestep(step, duration = sequence[step]['duration'], state = sequence[step]['state'])
    #         self.steps.append(s)
    #         self.add_knob(step)
    #         state[step] = s.duration
    #     self.hub.actuate({'sequencer': state})
