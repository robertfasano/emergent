from emergent.core import Hub
import time
from emergent.utilities.decorators import experiment
from scipy.stats import linregress
from scipy.optimize import curve_fit
import numpy as np
from emergent.devices.labjack import LabJack
import matplotlib.pyplot as plt
import requests
import pandas as pd
import json
import pickle
from emergent.artiq.sequencer import Sequencer
import logging as log

class MOT(Hub):
    def __init__(self, name, core = None):
        super().__init__(name, core = core)
        self.labjack = LabJack(params = {'devid': '470017907'}, name='labjack')

        ''' Power PMT and set gain '''
        self.labjack.AOut(0, .4)
        self.labjack.AOut(3,-5,TDAC=True)
        self.labjack.AOut(2,5, TDAC=True)

        ''' Define default experimental sequence. TTL channels are as follows:
            0: Slowing RF switch. TTL low enables power to AOM.
            1: Trap RF switch. TTL low enables power to AOM.
            2: Trap shutter. TTL high is open.
            3: Trap intensity servo. TTL low is on.
            4: Slowing intensity servo. TTL low is on.
            5: RF switch for doubled laser. TTL high is on.
            6: Shutter for doubled laser. TTL high is on.
            7: Slowing shutter. TTL high is on.
        '''
        loading_step = {'name': 'load',
            'duration': 1.5,
            'TTL': [2, 5, 6, 7],       # with inverts: [1, 2, 3, 4, 5, 6, 7]
            'ADC': [0],
            'DAC': {0: 0},
            'DDS': {}
           }
        delay_step = {'name': 'delay',
           'duration': 20e-3,
           'TTL': [2],                  # with inverts: [2, 3, 4]
           'ADC': [0],
           'DAC': {0: 0},
           'DDS': {}
          }
        probe_step = {'name': 'probe',
           'duration': 15e-3,
           'TTL': [5, 6],
           'ADC': [0],
           'DAC': {0: 0},
           'DDS': {}
          }

        steps = [loading_step, delay_step, probe_step]
        import json
        with open('/emergent/emergent/networks/gmot/sequences/transfer.json', 'r') as file:
            steps = json.load(file)
        self.sequencer = Sequencer('sequencer', hub = self, params = {'sequence': steps})
        self.sequencer.ttl = {0: 'slowing rf', 1: 'trap rf', 2: 'trap shutter', 3: 'trap servo', 4: 'slowing servo', 5: 'SHG rf', 6: 'SHG shutter', 7: 'slowing shutter', 8: 'test', 9: 'test', 10: 'test', 11: 'test', 12: 'test', 13: 'test', 14: 'test', 15: 'test',}
        self.sequencer.adc = {0: 'PMT'}
        self.sequencer.goto('load')

    def atom_number(self, signal, background):
        ''' Experimental variables '''
        probe_power = 4.05e-3
        Delta = -2*np.pi*(223.5/2-110)*1e6
        r = 6.5e-3
        SRS_gain = 5
        PMT_gain_voltage = 0.433

        ''' Constants '''
        Lambda = 399e-9
        c = 3e8
        h=6.626e-34
        Gamma=2*np.pi*29e6
        Energy=h*c/Lambda
        window_transmission = np.sqrt(0.86)
        solid_angle = 0.0355757

        P1 = probe_power*window_transmission
        P2 = probe_power*window_transmission**3
        Isat = 600
        beta1 = P1/(np.pi*r**2)/Isat
        beta2 = P2/(np.pi*r**2)/Isat
        R=Gamma/2*(beta1+beta2)/(1+beta1+beta2+4*Delta**2/Gamma**2)
        gain = self.PMT_calibration(PMT_gain_voltage)
        responsivity = 1e4*gain
        signal = (signal-background)/SRS_gain
        atom_number = 4*np.pi*signal/(solid_angle*responsivity*scattering_rate*energy*window_transmission)
        return atom_number

    def PMT_calibration(self, V):
        y1=5000
        y2=300000
        x1=.5
        x2=.8
        m=np.log10(y2/y1)/np.log10(x2/x1)
        c=y1/x1**m
        return c*x**m

    def artiq(self):
        if not hasattr(self.core, 'artiq_client'):           ## BAD! What if the client has been closed?
            log.warning('Connect to ARTIQ before submitting an experiment!')
            return -1
        requests.post('http://localhost:5000/artiq/run', json={})
        print('start:', time.time())
        self.core.artiq_client.emit('submit', self.devices['sequencer'].steps)
        while True:
            response = requests.get('http://localhost:5000/artiq/run').json()
            if 'result' in response:
                requests.post('http://localhost:5000/artiq/run', json={})
                break
        self.devices['sequencer'].current_step = self.devices['sequencer'].steps[-1]['name']

        data = pd.read_json(response['result'])
        data = data.set_index(pd.to_timedelta(data.index.values).total_seconds())
        return data

    def measure_loading(self):
        data = self.artiq()
        return data[data.index-data.index[0]<self.state['sequencer']['load']]

    def data_from(self, step_name, data):
        ''' Returns the section of a dataframe corresponding to a given timestep. '''
        ## get start of timestep
        start_time = 0
        for step in self.devices['sequencer'].steps:
            if step['name'] == step_name:
                break
            else:
                start_time += self.devices['sequencer'].state[step['name']]
        end_time = start_time + self.devices['sequencer'].state[step['name']]
        return data[(data.index >= start_time) & (data.index <= end_time)]

    @experiment
    def loading(self, state, params = {'quantity': ['slope', 'fluorescence', 'lifetime']}):
        self.actuate(state)
        # data = self.measure_loading()[0]
        data = self.artiq()
        data = self.data_from('load', data)
        fluorescence = (data.max()-data.min())[0]
        slope = np.polyfit(data.index, data.values, 1)[0][0]

        def model(t, A, tau):
            return A*(1-np.exp(-t/tau))

        popt, pcov = curve_fit(model, data.index.values, data[0].values, p0=(1,1))
        A_fit = popt[0]
        lifetime = popt[1]
        print('Fluorescence: %.0f mV'%(fluorescence*1000))
        print('Slope: %.0f mV/s'%(slope*1000))
        print('Lifetime: %.0f ms'%(lifetime*1000))

        if params['quantity'] == 'fluorescence':
            return -fluorescence
        elif params['quantity'] == 'slope':
            return -slope
        elif params['quantity'] == 'lifetime':
            return -lifetime

    @experiment
    def fluorescence(self, state, params = {}):
        self.actuate(state)
        data = self.measure_loading()[0]
        return -(data.max()-data.min())

    @experiment
    def slope(self, state, params = {}):
        self.actuate(state)
        data = self.measure_loading()[0]
        slope = np.polyfit(data.index, data.values, 1)[0][0]
        return -slope

    @experiment
    def lifetime(self, state, params = {}):
        self.actuate(state)
        data = self.measure_loading()[0]

        def model(t, A, tau):
            return A*(1-np.exp(-t/tau))

        popt, pcov = curve_fit(model, data.index.values, data[0].values, p0=(1,1))
        A_fit = popt[0]
        tau_fit = popt[1]

        return -tau_fit

    @experiment
    def transfer(self, state, params = {}):
        self.actuate(state)
        data = self.artiq()
        data1 = self.data_from('probe2', data).values.max()
        data2 = self.data_from('probe', data).values.max()
        print(data1/data2)

        return -(data1/data2)


    # @experiment
    # def transfer(self, state, params = {}):
    #     self.actuate(state)
    #     self.prepare()
    #
    #     ''' Prepare sequence '''
    #     for ch in ['trap rf', 'trap servo', 'trap shutter']:
    #         self.sequencer.steps[1].state[ch] = 1
    #
    #     self.sequencer.prepare()
    #     data = self.acquire()
    #     results = np.mean(data)
    #
    #     return -results
    #
    # @experiment
    # def no_transfer(self, state, params = {}):
    #     self.actuate(state)
    #
    #     self.prepare()
    #
    #     ''' Prepare sequence '''
    #     for ch in ['trap rf', 'trap servo', 'trap shutter']:
    #         self.sequencer.steps[1].state[ch] = 0
    #
    #     self.sequencer.prepare()
    #     data = self.acquire()
    #     results = np.mean(data)
    #
    #     return -results
