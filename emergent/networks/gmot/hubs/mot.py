from emergent.modules import Hub
import time
from emergent.utilities.decorators import experiment
from scipy.stats import linregress
from scipy.optimize import curve_fit
import numpy as np
from emergent.modules.parallel import ProcessHandler
from emergent.things.labjack import LabJack
import matplotlib.pyplot as plt
import requests
import pandas as pd
import json
import pickle
# from emergent.modules.sequencing import Sequencer
from emergent.artiq.emergent_sequencer import Sequencer

class MOT(Hub):
    def __init__(self, name, parent = None, network = None):
        super().__init__(name, parent = parent, network = network)
        self.process_manager = ProcessHandler()
        self.labjack = LabJack(params = {'devid': '470017907'}, name='labjack')

        # self.labjack.prepare_stream()
        # self.labjack.prepare_streamburst(channel=0)
        self.labjack.AOut(0, .4)
        self.labjack.AOut(3,-5,TDAC=True)
        self.labjack.AOut(2,5, TDAC=True)
        # self.TTL = LabJack(params = {'devid': '470016970'}, name = 'TTL')
        # self.trigger_labjack = LabJack(params = {'devid': '440010734'}, name='trigger')
        ''' Declare TTLs '''

        # self.switches['slowing rf'] = LabJackSwitch('slowing rf', {'labjack': self.TTL, 'channel': 1}, invert = True)         # artiq 0
        # self.switches['trap rf'] = LabJackSwitch('trap rf', {'labjack': self.TTL, 'channel': 2}, invert = True)               # 1
        # self.switches['trap shutter'] = LabJackSwitch('trap shutter', {'labjack': self.TTL, 'channel': 3})                    # 2

        # self.switches['trap servo'] = LabJackSwitch('trap servo', {'labjack': self.TTL, 'channel': 4}, invert = True)         # 3
                                                                                                                                # 4: slowing servo
        # self.switches['SHG rf'] = LabJackSwitch('SHG rf', {'labjack': self.TTL, 'channel': 5})                                # 5
        # self.switches['SHG shutter'] = LabJackSwitch('SHG shutter', {'labjack': self.TTL, 'channel': 6})                      # 6
        # self.switches['slowing shutter'] = LabJackSwitch('slowing shutter', {'labjack': self.TTL, 'channel': 7})

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

        self.sequencer = Sequencer('sequencer', parent = self, params = {'sequence': steps})
        self.sequencer.ttl = {0: 'slowing rf', 1: 'trap rf', 2: 'trap shutter', 3: 'trap servo', 4: 'slowing servo', 5: 'SHG rf', 6: 'SHG shutter', 7: 'slowing shutter', 8: 'test', 9: 'test', 10: 'test', 11: 'test', 12: 'test', 13: 'test', 14: 'test', 15: 'test',}
        self.sequencer.adc = {0: 'PMT'}
        self.sequencer.goto('load')

        self.result_buffer = []

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
        requests.post('http://localhost:5000/artiq/run', json={})
        print('start:', time.time())
        self.network.artiq_client.emit('submit', self.children['sequencer'].steps)
        while True:
            response = requests.get('http://localhost:5000/artiq/run').json()
            if 'result' in response:
                requests.post('http://localhost:5000/artiq/run', json={})
                break
        self.children['sequencer'].current_step = self.children['sequencer'].steps[-1]['name']

        data = pd.read_json(response['result'])
        return data

    @experiment
    def fluorescence(self, state, params = {}):
        self.actuate(state)
        data = self.artiq()
        print(data)

        return 0


    # @experiment
    # def slope(self, state, params = {}):
    #     self.actuate(state)
    #     print('Preparing sequence')
    #     self.prepare()
    #     self.sequencer.prepare()
    #     print('Acquiring data')
    #     data = self.acquire()
    #     print('Parsing data')
    #     load_time = self.sequencer.state['loading']/1000
    #     data = self.parse_data(data, self.sequencer.cycle_time, tmin=10e-3, tmax=load_time-10e-3)
    #     signal = np.max(data)-np.min(data)
    #     return -signal
    #
    # @experiment
    # def lifetime(self, state, params = {'t1': 6, 't2': 12, 'threshold': 0.2}):
    #     self.actuate(state)
    #
    #     self.prepare()
    #     signals = []
    #     for ch in ['trap rf', 'trap servo', 'trap shutter']:
    #         self.sequencer.steps[1].state[ch] = 1
    #     for i in range(2):
    #         print('Preparing sequence')
    #         ''' Prepare sequence '''
    #         if i == 0:
    #             self.sequencer.state['delay'] = params['t1']
    #         if i == 1:
    #             self.sequencer.state['delay'] = params['t2']
    #
    #
    #         self.sequencer.prepare()
    #         print('Running sequence')
    #         data = self.acquire()
    #         time_per_point = self.sequencer.cycle_time/len(data)
    #         print('Parsing data')
    #         loading_data = data[10:int(self.sequencer.state['loading']/1000/time_per_point)]
    #         loading_signal = np.max(loading_data)-np.min(loading_data)
    #         print('Loading signal:', loading_signal)
    #         probe_time = self.sequencer.state['loading']/1000 + self.sequencer.state['delay']/1000 + 1e-4
    #         end_probe_time = probe_time + self.sequencer.state['probe']/1000 - 1e-4
    #         data = data[int(probe_time/time_per_point):int(end_probe_time/time_per_point)]
    #         print('Max/min: %.2f, %.2f'%(np.max(data), np.min(data)))
    #         signal = np.max(data) - np.min(data)
    #         signals.append(signal)
    #
    #     short = signals[0]
    #     long = signals[1]
    #
    #     result = (short-long)/short
    #     print('Short delay: %.2f     Long delay: %.2f    Percent change: %.2f'%(signals[0], signals[1], result))
    #
    #     self.result_buffer.append(result)
    #     if len(self.result_buffer) > 5:
    #         del self.result_buffer[0]
    #     print('Last 5: %.2f +/- %.2f'%(np.mean(self.result_buffer), np.std(self.result_buffer)))
    #     if loading_signal < params['threshold']:
    #         return 1
    #     return result

    # def parse_data(self, data, duration, tmin = None, tmax = None):
    #     ''' Returns a subset of the data array corresponding to times
    #         greater than tmin and less than tmax. '''
    #     time_per_point = duration/len(data)
    #     min_point = int(tmin/time_per_point)
    #     max_point = int(tmax/time_per_point)
    #     return data[min_point:max_point]

    # def acquire(self, duration = None):
    #     if duration is None:
    #         duration = self.sequencer.cycle_time
    #     if self.labjack.stream_mode is not 'in-triggered':
    #         self.labjack.prepare_streamburst(0, trigger=0)
    #     self.stream_complete = False
    #     self.process_manager._run_thread(self.probe_trigger, args=(0,), stoppable=False)
    #     data = np.array(self.labjack.streamburst(duration))
    #     self.stream_complete = True
    #
    #     return data
    #
    # @experiment
    # def new_loading(self, state, params = {}):
    #     self.actuate(state)
    #
    #     self.prepare()
    #
    #     ''' Run sequence '''
    #     signals = []
    #     for i in range(2):
    #
    #         for ch in ['trap rf', 'trap servo', 'trap shutter']:
    #             self.sequencer.steps[1].state[ch] = i
    #
    #         self.sequencer.prepare()
    #         data = self.acquire()
    #
    #         probe_time = self.sequencer.state['loading']/1000 + self.sequencer.state['delay']/1000 + 1e-4
    #         end_probe_time = probe_time + self.sequencer.state['probe']/1000 - 1e-4
    #         # time_per_point = self.sequencer.cycle_time/len(data)
    #         # data = data[int(probe_time/time_per_point):int(end_probe_time/time_per_point)]
    #         data = self.parse_data(data, self.sequencer.cycle_time, tmin=probe_time, tmax=end_probe_time)
    #         print('Max/min: %.2f, %.2f'%(np.max(data), np.min(data)))
    #         signal = np.max(data) - np.min(data)
    #         signals.append(signal)
    #
    #     result = signals[1]/signals[0]
    #     print('Transfer: %.2f     No transfer: %.2f    Ratio: %.2f'%(signals[1], signals[0], result))
    #
    #     self.result_buffer.append(result)
    #     if len(self.result_buffer) > 5:
    #         del self.result_buffer[0]
    #     print('Last 5: %.2f +/- %.2f'%(np.mean(self.result_buffer), np.std(self.result_buffer)))
    #     return -result

    # def prepare(self):
    #     ''' Initial TTL state '''
    #     for switch in ['trap rf', 'SHG rf']:
    #         self.switches[switch].set(1)
    #     for switch in ['trap shutter', 'trap servo', 'SHG shutter']:
    #         self.switches[switch].set(0)
    #
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
    #
    # @experiment
    # def fluorescence(self, state, params = {'settling time': 0.1, 'duration': 0.25}):
    #     self.actuate(state)
    #     time.sleep(params['settling time'])
    #     # data = self.acquire(params['duration'])
    #
    #     return -self.labjack.AIn(0)
    #     # return -np.mean(data)
    #
    # def probe_trigger(self, trigger_delay = 0.1):
    #     i = 0
    #     while not self.stream_complete:
    #         i = i+1
    #         time.sleep(trigger_delay)
    #         self.trigger_labjack.DOut(4, i%2)

    # def ready(self):
    #     # self.TTL.DIO_STATE([self.PROBE_LIGHT, self.trap rf, self.trap shutter, self.trap servo, self.SHG rf, self.SHG shutter], [1, 0, 1, 0, 1, 1])
    #     for switch in ['trap rf', 'trap shutter', 'trap servo', 'SHG rf', 'SHG shutter']:
    #         self.switches[switch].set(1)
