''' This module allows definition and generation of TTL patterns. It also offers
    convenient options to control the TTL state through the GUI - every timestep
    added to the Sequencer appears as a knob whose duration can be altered, and
    a specific state can be set by right-clicking on the knob. '''
import time
import logging as log
import pandas as pd
import numpy as np
import json
from emergent.modules import Thing
import requests

class Sequence():
    ''' A container for a sequence of one or more Timesteps. '''
    def __init__(self, name, steps):
        self.name = name
        self.steps = steps

class Sequencer(Thing):
    def __init__(self, name, parent, params={'sequence': {}}):
        Thing.__init__(self, name, parent, params=params)
        self.channels = []
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
            self.children[step['name']].options = {'Go to %s'%step['name']: (goto_option(step['name']))}

            # for channel in step['TTL']:
            #     if channel not in self.channels:
            #         self.channels.append(channel)
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

    def get_switch_by_channel(self, ch):
        for switch in self.parent.switches.values():
            if switch.channel == ch:
                return switch

    def goto(self, step_name):
        ''' Go to a step specified by a string name. '''
        sequence = [self.get_step_by_name(step_name)]
        submit = {'sequence': sequence}
        requests.post('http://localhost:5000/artiq/run', json=submit)
        self.parent.network.artiq_client.emit('hold', sequence)

        self.current_step = step_name
        self.parent.network.socketIO.emit('timestep', step_name)

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
    #     for switch in self.parent.switches:
    #         state[switch] = 0
    #     step = Timestep(name, duration, state)
    #     self.steps.append(step)
    #
    #     goto_option = lambda s: lambda: self.goto(s)
    #     move_down_option = lambda s: lambda: self.move(s, 1)
    #     move_up_option = lambda s: lambda: self.move(s, -1)
    #     self.add_knob(step)
    #     self.children[step].options = {'Go to %s'%step: (goto_option(step))}
    #     self.children[step].options['Move up'] = move_up_option(step)
    #     self.children[step].options['Move down'] = move_down_option(step)
    #     self.parent.actuate({'sequencer': {step: 0}})
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
    #     knob_node = self.children[step]
    #     knob_node.leaf.move(n)
    #
    #     ''' Redraw grid '''
    #     if hasattr(self, 'grid'):
    #         self.grid.redraw()




    def open_grid(self):
        self.parent.network.socketIO.emit('sequencer', {'hub': self.parent.name})
