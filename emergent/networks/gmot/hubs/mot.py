from emergent.modules import Hub
import time
from utility import experiment
from scipy.stats import linregress
from scipy.optimize import curve_fit
import numpy as np
from emergent.modules.parallel import ProcessHandler
from emergent.things.labjack import LabJack
import matplotlib.pyplot as plt
from emergent.utility import Timer, Switch

class MOT(Hub):
    def __init__(self, name, parent = None, network = None):
        super().__init__(name, parent = parent, network = network)
        self.process_manager = ProcessHandler()
        self.labjack = LabJack(params = {'devid': '470017907'}, name='labjack')
        self.labjack.prepare_streamburst(channel=0)
        self.labjack.AOut(3,-5,HV=True)
        self.labjack.AOut(2,5, HV=True)
        self.TTL = LabJack(params = {'devid': '470016970'}, name = 'TTL')
        self.trigger_labjack = LabJack(params = {'devid': '440010734'}, name='trigger')
        self.timer = Timer()

        ''' Declare TTLs '''
        self.PROBE_LIGHT = 1 # integrator, probe rf switch TTL
        self.MOT_RF = 2  # slowing + cooling rf switches
        self.MOT_INTEGRATOR = 4   # slowing/cooling integrators
        self.MOT_SHUTTER = 3      # slowing/cooling shutters
        self.SHG_SWITCH = 5
        self.SHG_SHUTTER = 6

        self.switches['MOT_RF'] = Switch(self.TTL, 2, invert = True)
        self.switches['MOT_INTEGRATOR'] = Switch(self.TTL, 4, invert = True)
        self.switches['MOT_SHUTTER'] = Switch(self.TTL, 3)
        self.switches['SHG_SWITCH'] = Switch(self.TTL, 5)
        self.switches['SHG_SHUTTER'] = Switch(self.TTL, 6)

        ''' Enable MOT '''
        # self.TTL.DOut(self.PROBE_LIGHT, 1)     # disable probe
        # self.TTL.DOut(self.MOT_RF, 0)     # enable MOT AOM
        # self.TTL.DOut(self.MOT_SHUTTER,1)      # open MOT shutter
        # self.TTL.DOut(self.MOT_INTEGRATOR,0)      # enable MOT integrator

        for switch in ['MOT_RF', 'MOT_SHUTTER', 'MOT_INTEGRATOR']:
            self.switches[switch].set(1)

        # self.ignored = ['labjack', 'TTL', 'trigger_labjack']
        self.options['Load'] = self.ready
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

    def prepare_loading_pattern(self, cycle_time, params, accuracy = 1e-4):
        steps = cycle_time/accuracy
        sequence = {}

        sequence[self.PROBE_LIGHT] = [(0, 1),
                                      (params['loading time'], 0)]       # ch1
        sequence[self.MOT_RF] = [(0, 0),
                                 (params['loading time'], 1),
                                 (params['loading time']+params['AOM delay'], 0)]   #ch2
        sequence[self.MOT_INTEGRATOR] = [(0, 0), (params['loading time'], 1)]   # ch4
        sequence[self.MOT_SHUTTER] = [(0, 1), (params['loading time'], 0)]  #ch3
        y = self.TTL.generate_pattern(sequence, cycle_time, steps = steps)
        return y

    def prepare_hybrid_mot(self, cycle_time, params, accuracy = 1e-4):
        steps = cycle_time / accuracy
        sequence = {}

        sequence[self.PROBE_LIGHT] = [(0, 0)]       # ch1


        ''' Helper beam sequence '''
        ''' Turn off light after loading, wait for a programmable delay, then back on to probe.
            Finally, turn off light again and shutter it. '''
        sequence[self.MOT_RF] = [(0, 0),
                                 (params['loading time'], 1),
                                 (params['loading time'] + params['probe delay'], 0),
                                 (params['loading time'] + params['probe delay'] + params['probe time'], 1),
                                 (params['loading time']+ params['probe delay'] + params['probe time'] + params['AOM delay'], 0)]   # 0 = ON
        sequence[self.MOT_INTEGRATOR] = [(0, 0),
                                 (params['loading time'], 1),
                                 (params['loading time'] + params['probe delay'], 0),
                                 (params['loading time'] + params['probe delay'] + params['probe time'], 1)]   # 0 = ON
        sequence[self.MOT_SHUTTER] = [(0, 1), (params['loading time']+params['probe delay'] + params['probe time'], 0)]  # start closing shutter immediately after probing


        ''' gMOT sequence '''
        ''' For shot 1, turn off light after gMOT loading time set in the GUI. For shot 2, set gMOT loading time
            to end 100 us before the helper probe pulse '''
        sequence[self.SHG_SWITCH] = [(0, 1),
                                     (params['gMOT loading time'], 0),
                                     (params['gMOT loading time'] + params['AOM delay'], 1)]
        sequence[self.SHG_SHUTTER] = [(0, 1),
                                     (params['gMOT loading time'], 0)]

        y = self.TTL.generate_pattern(sequence, cycle_time, steps = steps)
        return y


    def load_MOT(self):
        ''' Switch to the loading stage '''
        self.TTL.DIO_STATE([self.PROBE_LIGHT, self.MOT_RF, self.MOT_SHUTTER, self.MOT_INTEGRATOR], [1, 0, 1, 0])

    def probe_MOT(self):
        ''' Switch to the probing stage '''
        self.TTL.DIO_STATE([self.PROBE_LIGHT, self.MOT_RF, self.MOT_SHUTTER, self.MOT_INTEGRATOR], [0, 1, 0, 1])


    @experiment
    def loading_fluorescence(self, state, params = {'loading delay': 0.1}):
        self.TTL.DIO_STATE([self.MOT_RF, self.MOT_SHUTTER, self.MOT_INTEGRATOR], [1, 0, 1])        # turn MOT off

        for key in ['loading time', 'probe time', 'probe delay', 'gate time', 'AOM delay']:
            params[key] = self.children['loader'].state[key]/1000
        time.sleep(params['AOM delay'])
        self.TTL.DOut(self.MOT_RF, 0)        # switch RF back on to avoid thermalization, but keep shutter closed
        time.sleep(params['loading delay']-params['AOM delay'])

        self.TTL.DIO_STATE([self.MOT_RF, self.MOT_SHUTTER, self.MOT_INTEGRATOR], [0, 1, 0])        # turn MOT on
        light_background = self.labjack.AIn(0)
        time.sleep(params['loading time'])
        atom_fluorescence = self.labjack.AIn(0)

        signal = atom_fluorescence - light_background

        return -signal

    def run_sequence(self, cycle_time, sequence, stream_in_time):
        y = self.TTL.array_to_bitmask(sequence, list(range(1, sequence.shape[1]+1)))

        ''' Write TTL pattern to labjack '''
        sequence, scanRate = self.TTL.resample(np.atleast_2d(y).T, cycle_time)
        self.TTL.stream_out(['FIO_STATE'], sequence, scanRate, loop=0)

        ''' Queue triggered stream-in on self.labjack '''
        if self.labjack.stream_mode is not 'in-triggered':
            self.labjack.prepare_streamburst(0, trigger=0)
        self.stream_complete = False
        self.process_manager._run_thread(self.probe_trigger, args=(0,), stoppable=False)
        data = np.array(self.labjack.streamburst(stream_in_time))
        self.stream_complete = True

        return data

    @experiment
    def load_hybrid_MOT(self, state, params = {}):
        results = []
        self.actuate(state)

        ''' Prepare TTL stream '''
        self.TTL.prepare_digital_stream([1, 2, 3, 4, 5, 6])

        ''' Initial state '''
        self.TTL.DOut(self.PROBE_LIGHT, 1)     # disable probe
        self.TTL.DOut(self.MOT_RF, 0)     # enable MOT AOM
        self.TTL.DOut(self.MOT_SHUTTER,0)      # close MOT shutter
        self.TTL.DOut(self.MOT_INTEGRATOR,1)      # disable MOT integrator
        self.TTL.DOut(self.SHG_SWITCH, 1)
        self.TTL.DOut(self.SHG_SHUTTER, 0)

        self.TTL.prepare_stream_out(trigger=0)
        for key in ['loading time', 'probe time', 'probe delay', 'gate time', 'AOM delay']:
            params[key] = self.children['loader'].state[key]/1000
        cycle_time = params['loading time'] + params['probe delay'] + params['probe time'] + params['AOM delay'] + 0.01

        for i in range(2):
            if i == 0:
                params['gMOT loading time'] = params['loading time']
            elif i == 1:
                params['gMOT loading time'] = params['loading time'] + params['probe delay'] - 100e-6
            y = self.prepare_hybrid_mot(cycle_time, params)
            stream_time = params['loading time'] + params['probe delay'] + params['probe time']
            data = self.run_sequence(cycle_time, y, stream_time)

            ''' Process data '''
            time_per_point = stream_time / len(data)
            first_point = int((stream_time - params['probe time']) / time_per_point)
            duration = int(params['probe time']/time_per_point*.9)
            data = data[first_point:first_point+duration]
            t = np.linspace(0, params['probe time'], len(data))

            results.append(np.mean(data))


        result = results[1] - results[0]
        print(results, result)
        return -result

    @experiment
    def loading_slope(self, state, params = {'samples': 1}):
        results = []
        self.actuate(state)

        ''' Prepare TTL stream '''
        self.TTL.prepare_digital_stream([1, 2, 3, 4])

        ''' Initial state '''
        self.TTL.DOut(self.PROBE_LIGHT, 1)     # disable probe
        self.TTL.DOut(self.MOT_RF, 0)     # enable MOT AOM
        self.TTL.DOut(self.MOT_SHUTTER,0)      # close MOT shutter
        self.TTL.DOut(self.MOT_INTEGRATOR,1)      # disable MOT integrator
        self.TTL.DOut(self.SHG_SWITCH, 1)
        self.TTL.DOut(self.SHG_SHUTTER, 1)

        self.TTL.prepare_stream_out(trigger=0)

        for i in range(int(params['samples'])):
            ''' Form
             TTL pattern from GUI '''
            for key in ['loading time', 'probe time', 'probe delay', 'gate time', 'AOM delay']:
                params[key] = self.children['loader'].state[key]/1000
            cycle_time = params['loading time'] + params['AOM delay']
            # self.timer.log('Preparing pattern')
            y = self.prepare_loading_pattern(cycle_time, params)

            y = self.TTL.array_to_bitmask(y, [1,2,3,4])
            # self.timer.log('Pattern prepared')

            ''' Write TTL pattern to thing '''
            sequence, scanRate = self.TTL.resample(np.atleast_2d(y).T, cycle_time)
            # self.timer.log('Resampled')
            self.TTL.stream_out(['FIO_STATE'], sequence, scanRate, loop=0)
            # self.timer.log('Wrote to labjack')
            ''' Queue triggered stream-in on self.labjack '''
            if self.labjack.stream_mode is not 'in-triggered':
                # print('Preparing burst stream.')
                self.labjack.prepare_streamburst(0, trigger=0)
            self.stream_complete = False
            self.process_manager._run_thread(self.probe_trigger, args=(0,), stoppable=False)
            data = np.array(self.labjack.streamburst(params['loading time']))

            self.stream_complete = True
            ''' Process data '''
            time_per_point = params['loading time'] / len(data)
            data = data[int(params['probe delay']/time_per_point)::]
            t = np.linspace(params['probe delay'], params['loading time'], len(data))

            fit = linregress(t, data)
            slope = fit[0]
            intercept = fit[1]
            results.append(slope)

        mean = np.mean(results)
        error = np.std(results)/np.sqrt(len(results))
        print(mean*1000, error*1000)
        return -mean

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
            ''' Form
             TTL pattern from GUI '''
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
        # self.TTL.DIO_STATE([self.PROBE_LIGHT, self.MOT_RF, self.MOT_SHUTTER, self.MOT_INTEGRATOR, self.SHG_SWITCH, self.SHG_SHUTTER], [1, 0, 1, 0, 1, 1])
        for switch in ['MOT_RF', 'MOT_SHUTTER', 'MOT_INTEGRATOR', 'SHG_SWITCH', 'SHG_SHUTTER']:
            self.switches[switch].set(1)

    @experiment
    def test_refactor(self, state, params = {}):
        cls = HybridMOT()

class HybridMOT():
    def __init__(self, params):
        self.params = params

    def execute(self):
        self.prepare()
        data = self.run()
        return self.analyze(data)

    def prepare(self):
        ''' Initialize the non-realtime state '''
        results = []
        self.actuate(state)

        ''' Prepare TTL stream '''
        self.TTL.prepare_digital_stream([1, 2, 3, 4, 5, 6])

        ''' Initial state '''
        self.TTL.DOut(self.PROBE_LIGHT, 1)     # disable probe
        self.TTL.DOut(self.MOT_RF, 0)     # enable MOT AOM
        self.TTL.DOut(self.MOT_SHUTTER,0)      # close MOT shutter
        self.TTL.DOut(self.MOT_INTEGRATOR,1)      # disable MOT integrator
        self.TTL.DOut(self.SHG_SWITCH, 1)
        self.TTL.DOut(self.SHG_SHUTTER, 0)

        self.TTL.prepare_stream_out(trigger=0)
        for key in ['loading time', 'probe time', 'probe delay', 'gate time', 'AOM delay']:
            params[key] = self.children['loader'].state[key]/1000
        cycle_time = params['loading time'] + params['probe delay'] + params['probe time'] + params['AOM delay'] + 0.01
        y = self.prepare_hybrid_mot(cycle_time, params)
        stream_time = params['loading time'] + params['probe delay'] + params['probe time']

        return

    def run(self):
        ''' Execute a sequence in real-time and return a data array '''
        data = self.run_sequence(cycle_time, y, stream_time)

        return data

    def analyze(self, data):
        ''' Process the data to return some useful result '''
        time_per_point = stream_time / len(data)
        first_point = int((stream_time - params['probe time']) / time_per_point)
        duration = int(params['probe time']/time_per_point*.9)
        data = data[first_point:first_point+duration]
        t = np.linspace(0, params['probe time'], len(data))
        return np.mean(data)
