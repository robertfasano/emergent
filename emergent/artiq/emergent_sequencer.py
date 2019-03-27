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
import os

class Sequencer(Thing):
    def __init__(self, name, parent, params={'sequence': {}}):
        Thing.__init__(self, name, parent, params=params)
        self.channels = []
        if 'labjack' in params:
            self.labjack = params['labjack']
        self.options['Show grid'] = self.open_grid

        goto_option = lambda s: lambda: self.goto(s)

        self.ttl = []
        self.adc = []
        self.dac = []
        for step in params['sequence']:
            self.add_knob(step['name'])
            self.children[step['name']].options = {'Go to %s'%step['name']: (goto_option(step['name']))}

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
        self.sequences = {'default': self.steps}
        self.cycle_time = 0
        self.current_step = None
        self.current_sequence = 'default'


        ''' Load saved sequences '''
        saved_sequences = self.get_saved_sequences()
        for name in saved_sequences:
            self.load(name)
        self.activate('default')

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
        if hasattr(self.parent.network, 'artiq_client'):
            self.parent.network.artiq_client.emit('hold', sequence)

        self.current_step = step_name
        self.parent.network.emit('timestep', {'name': step_name})

    def add_step(self, name, position = -1):
        step = {'name': name,
                'duration': 0,
                'TTL': [],
                'ADC': [],
                'DAC': {},
                'DDS': {}}
        if self.get_step_by_name(name) is not None:
            log.warn('Step already exists!')
            return
        self.steps.append(step)
        self.add_knob(name)
        time.sleep(3/1000)      # delay to make sure knob registers in GUI

        if position < 0:
            self.move(name, -(position+1))
        else:
            self.move(name, -(len(self.steps)-position-1))

    def move(self, step, n):
        ''' Moves the passed step (integer or string) n places to the left (negative n)
            or right (positive n). '''
        i = 0
        for s in self.steps:
            if s['name'] == step:
                break
            i += 1
        if (i+n)<0 or (i+n) > len(self.steps)-1:
            return

        self.steps.insert(i+n, self.steps.pop(i))
        self.parent.network.emit('sequence update')
        self.parent.network.emit('sequence reorder', {'name': step, 'n': n})

    def open_grid(self):
        self.parent.network.emit('sequencer', {'hub': self.parent.name})

    def get_saved_sequences(self):
        path = self.parent.network.path['sequences']
        if not os.path.exists(path):
            os.makedirs(path)

        return [x.split('.json')[0] for x in os.listdir(path) if 'json' in x]

    def load(self, name):
        ''' Load a sequence from file '''
        if name == 'default':
            return
        path = self.parent.network.path['sequences']
        with open(path+'%s.json'%name, 'r') as file:
            self.steps = json.load(file)
        self.store(name)
        # self.parent.network.emit('sequence update')

    def save(self, name, steps=None):
        ''' Save the current sequence to file '''
        if name == 'default':
            return
        if steps is None:
            steps = self.steps
        path = self.parent.network.path['sequences']
        with open(path+'%s.json'%name, 'w') as file:
            json.dump(self.steps, file)

    def activate(self, name):
        self.steps = self.sequences[name]
        self.parent.network.emit('sequence update')
        self.current_sequence = name

    def store(self, name, steps=None):
        if steps is None:
            steps = self.steps
        self.sequences[name] = steps
        self.current_sequence = name
        self.save(name, steps)

    def delete(self, name):
        ''' Remove a sequence by name from self.sequences and delete its associated file '''
        if name == 'default':
            return
        del self.sequences[name]
        path = self.parent.network.path['sequences']
        os.remove(path+'%s.json'%name)
