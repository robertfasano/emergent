from emergent.modules import Hub
import time
from utility import experiment
from scipy.stats import linregress
from scipy.optimize import curve_fit
import numpy as np
from emergent.modules.parallel import ProcessHandler
from emergent.things.labjack import LabJack
import matplotlib.pyplot as plt
from emergent.utility import Timer

class MOT(Hub):
    def __init__(self, name, parent = None, path='.'):
        super().__init__(name, parent = parent, path=path)
        self.process_manager = ProcessHandler()
        self.labjack = LabJack(devid='470017907', name='labjack')
        self.labjack.prepare_streamburst(channel=0)
        self.labjack.AOut(3,-5,HV=True)
        self.labjack.AOut(2,5, HV=True)
        self.TTL = LabJack(devid='470016970', name = 'TTL')
        self.trigger_labjack = LabJack(devid='440010734', name='trigger')
        self.timer = Timer()

        self.PROBE_LIGHT = 1 #done
        self.MOT_RF = 2
        self.MOT_INTEGRATOR = 4
        self.ADC = self.MOT_INTEGRATOR
        self.MOT_SHUTTER = 3

        ''' Enable MOT '''
        self.TTL.DOut(self.PROBE_LIGHT, 1)     # disable probe
        self.TTL.DOut(self.MOT_RF, 0)     # enable MOT AOM
        self.TTL.DOut(self.MOT_SHUTTER,1)      # open MOT shutter
        self.TTL.DOut(self.MOT_INTEGRATOR,0)      # enable MOT integrator

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

    def prepare_pattern(self, cycle_time, params, accuracy = 1e-4):
        steps = cycle_time/accuracy
        sequence = {}

        sequence[self.PROBE_LIGHT] = [(0, 1),
                                      (params['loading time']+params['probe delay'], 0),
                                      (params['loading time']+params['probe delay']+params['probe time'], 1)]       # ch1
        sequence[self.MOT_RF] = [(0, 0),
                                 (params['loading time'], 1),
                                 (params['loading time']+params['AOM delay'], 0)]   #ch2
        sequence[self.MOT_INTEGRATOR] = [(0, 0), (params['loading time'], 1)]   # ch4
        sequence[self.MOT_SHUTTER] = [(0, 1), (params['loading time'], 0)]  #ch3
        y = self.TTL.generate_pattern(sequence, cycle_time, steps = steps)
        return y

    def load_MOT(self):
        ''' Switch to the loading stage '''
        self.TTL.DIO_STATE([self.PROBE_LIGHT, self.MOT_RF, self.MOT_SHUTTER, self.MOT_INTEGRATOR], [1, 0, 1, 0])

    def probe_MOT(self):
        ''' Switch to the probing stage '''
        self.TTL.DIO_STATE([self.PROBE_LIGHT, self.MOT_RF, self.MOT_SHUTTER, self.MOT_INTEGRATOR], [0, 1, 0, 1])

    @experiment
    def probe(self, state, params = {'samples': 1}):
        results = []
        self.actuate(state)

        ''' Prepare TTL stream '''
        self.TTL.prepare_digital_stream([1, 2, 3, 4])

        ''' Initial state '''
        self.TTL.DOut(self.PROBE_LIGHT, 1)     # disable probe
        self.TTL.DOut(self.MOT_RF, 0)     # enable MOT AOM
        self.TTL.DOut(self.MOT_SHUTTER,0)      # close MOT shutter
        self.TTL.DOut(self.MOT_INTEGRATOR,1)      # disable MOT integrator

        self.TTL.prepare_stream_out(trigger=0)

        for i in range(int(params['samples'])):
            ''' Form TTL pattern from GUI '''
            for key in ['loading time', 'probe time', 'probe delay', 'gate time', 'AOM delay']:
                params[key] = self.children['loader'].state[key]/1000
            cycle_time = params['loading time'] + params['probe delay'] + params['probe time'] + 0.01
            self.timer.log('Preparing pattern')
            y = self.prepare_pattern(cycle_time, params)

            y = self.TTL.array_to_bitmask(y, [1,2,3,4])
            self.timer.log('Pattern prepared')

            ''' Write TTL pattern to thing '''
            sequence, scanRate = self.TTL.resample(np.atleast_2d(y).T, cycle_time)
            self.timer.log('Resampled')
            self.TTL.stream_out(['FIO_STATE'], sequence, scanRate, loop=0)
            self.timer.log('Wrote to labjack')
            ''' Queue triggered stream-in on self.labjack '''
            if self.labjack.stream_mode is not 'in-triggered':
                print('Preparing burst stream.')
                self.labjack.prepare_streamburst(0, trigger=0)
            self.stream_complete = False
            self.process_manager._run_thread(self.probe_trigger, args=(0,), stoppable=False)
            data = np.array(self.labjack.streamburst(params['probe time']))

            self.stream_complete = True
            ''' Process data '''
            time_per_point = params['probe time']/len(data)
            max_point = np.argmax(data)
            data = data[max_point:max_point+int(params['gate time']/time_per_point)]
            results.append(np.mean(data))

        mean = np.mean(results)
        error = np.std(results)/np.sqrt(len(results))
        print(mean*1000, error*1000)
        return -mean

    @experiment
    def fluorescence(self, state, params = {'settling time': 0.1, 'duration': 0.25}):
        self.actuate(state)
        time.sleep(params['settling time'])
        data = self.labjack.streamburst(duration=params['duration'], operation = None)
        print(str(np.mean(data)*1000) + '+/-' + str(np.std(data)*1000))
        return -np.mean(data)

    def probe_trigger(self, trigger_delay = 0.1):
        i = 0
        while not self.stream_complete:
            i = i+1
            time.sleep(trigger_delay)
            self.trigger_labjack.DOut(4, i%2)
