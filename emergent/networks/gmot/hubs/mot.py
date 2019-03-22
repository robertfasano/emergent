from emergent.modules import Hub
import time
from emergent.utilities.decorators import experiment
from scipy.stats import linregress
from scipy.optimize import curve_fit
import numpy as np
from emergent.modules.parallel import ProcessHandler
from emergent.things.labjack import LabJack, LabJackSwitch
import matplotlib.pyplot as plt
from emergent.utilities.testing import Timer
# from emergent.modules.sequencing import Sequencer
from emergent.artiq.emergent_sequencer import Sequencer

class MOT(Hub):
    def __init__(self, name, parent = None, network = None):
        super().__init__(name, parent = parent, network = network)
        self.process_manager = ProcessHandler()
        self.labjack = LabJack(params = {'devid': '470017907'}, name='labjack')
        self.labjack.prepare_stream()
        self.labjack.prepare_streamburst(channel=0)
        self.labjack.AOut(0, .4)
        self.labjack.AOut(3,-5,TDAC=True)
        self.labjack.AOut(2,5, TDAC=True)
        self.TTL = LabJack(params = {'devid': '470016970'}, name = 'TTL')
        self.trigger_labjack = LabJack(params = {'devid': '440010734'}, name='trigger')
        self.timer = Timer()

        ''' Declare TTLs '''

        self.switches['trap rf'] = LabJackSwitch('trap rf', {'labjack': self.TTL, 'channel': 2}, invert = True)
        self.switches['trap servo'] = LabJackSwitch('trap servo', {'labjack': self.TTL, 'channel': 4}, invert = True)
        self.switches['trap shutter'] = LabJackSwitch('trap shutter', {'labjack': self.TTL, 'channel': 3})
        self.switches['SHG rf'] = LabJackSwitch('SHG rf', {'labjack': self.TTL, 'channel': 5})
        self.switches['SHG shutter'] = LabJackSwitch('SHG shutter', {'labjack': self.TTL, 'channel': 6})

        self.switches['slowing shutter'] = LabJackSwitch('slowing shutter', {'labjack': self.TTL, 'channel': 7})
        self.switches['slowing rf'] = LabJackSwitch('slowing rf', {'labjack': self.TTL, 'channel': 1}, invert = True)

        steps = [{'name': 'loading', 'state': {'trap rf': 1, 'trap servo': 1, 'trap shutter': 1, 'SHG rf': 1, 'SHG shutter': 1, 'slowing shutter': 1, 'slowing rf': 1}},
                 {'name': 'delay', 'state': {'trap rf': 1, 'trap servo': 1, 'trap shutter': 1, 'SHG rf': 0, 'SHG shutter': 1, 'slowing shutter': 0, 'slowing rf': 0}},
                 {'name': 'probe', 'state': {'trap rf': 0, 'trap servo': 0, 'trap shutter': 0, 'SHG rf': 1, 'SHG shutter': 1, 'slowing shutter': 0, 'slowing rf': 0}},
                 {'name': 'rf off', 'state': {'trap rf': 0, 'trap servo': 0, 'trap shutter': 0, 'SHG rf': 0, 'SHG shutter': 0, 'slowing shutter': 0, 'slowing rf': 0}},
                 {'name': 'rf on', 'state': {'trap rf': 1, 'trap servo': 0, 'trap shutter': 0, 'SHG rf': 1, 'SHG shutter': 0, 'slowing shutter': 0, 'slowing rf': 1}}]

        loading_step = {'name': 'load',
            'duration': 1.5,
            'TTL': [1, 2, 3, 4, 5, 6, 7],
            'ADC': [0],
            'DAC': {},
            'DDS': {}
           }
        delay_step = {'name': 'delay',
           'duration': 20e-3,
           'TTL': [2, 3, 4],
           'ADC': [0],
           'DAC': {},
           'DDS': {}
          }
        probe_step = {'name': 'probe',
           'duration': 15e-3,
           'TTL': [5, 6],
           'ADC': [0],
           'DAC': {},
           'DDS': {}
          }

        steps = [loading_step, delay_step, probe_step]
        print('MOT: Preparing initial state.')

        self.sequencer = Sequencer('sequencer', parent = self, params = {'labjack': self.TTL, 'sequence': steps})
        self.sequencer.ttl = {1: 'slowing rf', 2: 'trap rf', 3: 'trap shutter', 4: 'trap servo', 5: 'SHG rf', 6: 'SHG shutter', 7: 'slowing shutter'}
        self.sequencer.adc = {0: 'PMT'}
        self.sequencer.goto('load')

        self.options['Load'] = self.ready

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

    @experiment
    def new_loading(self, state, params = {}):
        self.actuate(state)

        ''' Initial TTL state '''
        for switch in ['trap rf', 'SHG rf']:
            self.switches[switch].set(1)
        for switch in ['trap shutter', 'trap servo', 'SHG shutter']:
            self.switches[switch].set(0)
        signals = []
        for i in range(2):
            ''' Prepare sequence '''
            for ch in ['trap rf', 'trap servo', 'trap shutter']:
                self.sequencer.steps[1].state[ch] = i

            self.sequencer.prepare()

            if self.labjack.stream_mode is not 'in-triggered':
                self.labjack.prepare_streamburst(0, trigger=0)
            self.stream_complete = False
            self.process_manager._run_thread(self.probe_trigger, args=(0,), stoppable=False)
            data = np.array(self.labjack.streamburst(self.sequencer.cycle_time))
            self.stream_complete = True

            probe_time = self.sequencer.state['loading']/1000 + self.sequencer.state['delay']/1000 + 1e-4
            end_probe_time = probe_time + self.sequencer.state['probe']/1000 - 1e-4
            time_per_point = self.sequencer.cycle_time/len(data)
            data = data[int(probe_time/time_per_point):int(end_probe_time/time_per_point)]
            print('Max/min: %.2f, %.2f'%(np.max(data), np.min(data)))
            signal = np.max(data) - np.min(data)
            signals.append(signal)


        result = signals[1]/signals[0]
        print('Transfer: %.2f     No transfer: %.2f    Ratio: %.2f'%(signals[1], signals[0], result))

        self.result_buffer.append(result)
        if len(self.result_buffer) > 5:
            del self.result_buffer[0]
        print('Last 5: %.2f +/- %.2f'%(np.mean(self.result_buffer), np.std(self.result_buffer)))
        return -result

    @experiment
    def transfer(self, state, params = {}):
        self.actuate(state)

        ''' Initial TTL state '''
        for switch in ['trap rf', 'SHG rf']:
            self.switches[switch].set(1)
        for switch in ['trap shutter', 'trap servo', 'SHG shutter']:
            self.switches[switch].set(0)

        ''' Prepare sequence '''
        for ch in ['trap rf', 'trap servo', 'trap shutter']:
            self.sequencer.steps[1].state[ch] = 1

        self.sequencer.prepare()

        if self.labjack.stream_mode is not 'in-triggered':
            self.labjack.prepare_streamburst(0, trigger=0)
        self.stream_complete = False
        self.process_manager._run_thread(self.probe_trigger, args=(0,), stoppable=False)
        data = np.array(self.labjack.streamburst(self.sequencer.cycle_time))
        self.stream_complete = True

        results = np.mean(data)

        return -results

    @experiment
    def no_transfer(self, state, params = {}):
        self.actuate(state)

        ''' Initial TTL state '''
        for switch in ['trap rf', 'SHG rf']:
            self.switches[switch].set(1)
        for switch in ['trap shutter', 'trap servo', 'SHG shutter']:
            self.switches[switch].set(0)

        ''' Prepare sequence '''
        for ch in ['trap rf', 'trap servo', 'trap shutter']:
            self.sequencer.steps[1].state[ch] = 0

        self.sequencer.prepare()

        if self.labjack.stream_mode is not 'in-triggered':
            self.labjack.prepare_streamburst(0, trigger=0)
        self.stream_complete = False
        self.process_manager._run_thread(self.probe_trigger, args=(0,), stoppable=False)
        data = np.array(self.labjack.streamburst(self.sequencer.cycle_time))
        self.stream_complete = True

        results = np.mean(data)

        return -results

    @experiment
    def fluorescence(self, state, params = {'settling time': 0.1, 'duration': 0.25}):
        self.actuate(state)
        time.sleep(params['settling time'])
        # data = self.labjack.streamburst(duration=params['duration'], operation = None)
        # print(str(np.mean(data)*1000) + '+/-' + str(np.std(data)*1000))

        return -self.labjack.AIn(0)
        # return -np.mean(data)

    def probe_trigger(self, trigger_delay = 0.1):
        i = 0
        while not self.stream_complete:
            i = i+1
            time.sleep(trigger_delay)
            self.trigger_labjack.DOut(4, i%2)

    def ready(self):
        # self.TTL.DIO_STATE([self.PROBE_LIGHT, self.trap rf, self.trap shutter, self.trap servo, self.SHG rf, self.SHG shutter], [1, 0, 1, 0, 1, 1])
        for switch in ['trap rf', 'trap shutter', 'trap servo', 'SHG rf', 'SHG shutter']:
            self.switches[switch].set(1)
