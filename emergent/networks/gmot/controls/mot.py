from emergent.archetypes.node import Control
import time
from utility import experiment
from scipy.stats import linregress
from scipy.optimize import curve_fit
import numpy as np
from emergent.archetypes.parallel import ProcessHandler
from emergent.devices.labjackT7 import LabJack
import matplotlib.pyplot as plt
from emergent.utility import Timer

class MOT(Control):
    def __init__(self, name, parent = None, path='.'):
        super().__init__(name, parent = parent, path=path)
        self.process_manager = ProcessHandler()
        self.trigger_labjack = LabJack(devid='440010734', name = 'trigger')
        self.timer = Timer()
    def add_labjack(self, labjack):
        self.labjack = labjack
        self.labjack.prepare_streamburst(channel=0)
        self.labjack.AOut(3,-5,HV=True)
        self.labjack.AOut(2,5, HV=True)
        self.set_offset(0)

    def set_offset(self, offset):
        self.offset = offset
        self.labjack.AOut(1,offset)

    def center_signal(self, threshold = .010, gain = .1):
        ''' Applies an offset with DAC1 to zero the signal received on AIN0. '''
        signal = 0
        oscillation_count = 0
        while True:
            last_signal = signal
            signal = self.labjack.AIn(0)
            if np.sign(last_signal) != np.sign(signal):
                oscillation_count += 1
            else:
                oscillation_count = 0
            if oscillation_count > 2:
                gain *= .5
            if np.abs(signal) < threshold:
                break
            print('offset: %f to %f'%(self.offset, self.offset+gain))

            self.set_offset(self.offset+gain*signal)
            print('signal:',signal)

    @experiment
    def probe_pulse(self, state, params = {'stream step': 0.001, 'probe intensity': 0.3, 'integration time': 0.005, 'loading time': 1, 'probe time': 0.1, 'trigger delay': 0.001}):
        ''' Queue triggered stream-out on intensity servo channels '''
        if 'servo' in state:
            state['servo']['V0'] = 0
        self.actuate(state)

        cycle_time = params['loading time'] + params['probe time']
        servo = self.children['servo']
        t = np.linspace(0,cycle_time, int(1e4))
        ''' Minimum number of samples is the cycle time divided by the required precision '''
        precision = params['stream step']
        samples = int(cycle_time / precision)

        self.timer.log('Preparing probe stream')
        probe_labjack = servo.labjack[0]
        y = np.zeros((len(t),2))
        y[t>params['loading time'], 0] = params['probe intensity']
        probe_labjack.prepare_stream_out(trigger=0)
        sequence, scanRate = probe_labjack.resample(y, cycle_time, max_samples = samples)

        self.timer.log('Writing probe stream')
        probe_labjack.stream_out([0,1], sequence, scanRate, loop=0)

        self.timer.log('Preparing trap stream')
        trap_labjack = servo.labjack[1]
        y = np.zeros((len(t),2))
        y[t<params['loading time'], 0] = self.state['servo']['V2']
        y[t<params['loading time'], 1] = self.state['servo']['V3']
        trap_labjack.prepare_stream_out(trigger=0)
        sequence, scanRate = trap_labjack.resample(y, cycle_time, max_samples = samples)
        self.timer.log('Writing trap stream')
        trap_labjack.stream_out([0,1], sequence, scanRate, loop=0)

        ''' Queue triggered stream-in on self.labjack '''
        self.timer.log('Preparing input stream')
        if self.labjack.stream_mode is not 'in-triggered':
            self.labjack.prepare_streamburst(0, trigger=0)
        self.process_manager._run_thread(self.probe_trigger, args=(params['trigger delay'],), stoppable=False)
        self.timer.log('Running input stream')
        data = self.labjack.streamburst(cycle_time)
        self.timer.log('Finished streaming')
        time_per_point = cycle_time/len(data)
        probe_point = int(params['loading time']/time_per_point)
        integration_points = int(params['integration time']/time_per_point)

        value = np.array(data)[probe_point:probe_point+integration_points].sum()
        print(np.max(data))
        # plt.plot(data)
        # plt.show()
        return -np.max(data)

    @experiment
    def pulsed_slowing(self, state = None, params = {'pulse time': 0.5, 'settling time': 0.05}):
        if state is not None:
            self.actuate(state)
        self.children['servo'].lock(2,0)
        self.labjack.DOut(4,0)
        low = self.labjack.streamburst(duration=params['pulse time'], operation = 'mean')
        self.labjack.DOut(4,1)
        self.children['servo'].lock(2,1)
        high = self.labjack.streamburst(duration=params['pulse time'], operation = 'mean')
        return -high    # low is subtracted out by SRS

    @experiment
    def fluorescence(self, state, params = {'settling time': 0.1, 'duration': 0.25}):
        self.actuate(state)
        time.sleep(params['settling time'])
        data = self.labjack.streamburst(duration=params['duration'], operation = None)
        print(str(np.mean(data)) + '+/-' + str(np.std(data)))
        return -np.mean(data)

    @experiment
    def probe_switch(self, state, params = {'loading time': 1, 'probe time': 0.1, 'trigger delay': 0.01}):
        ''' Stream on the digital channels to switch RF switches '''

    def probe_trigger(self, trigger_delay = 0.001):
        for i in range(10):
            time.sleep(trigger_delay)
            self.trigger_labjack.DOut(4, i%2)

    def wave(self, frequency=2):
        V = 3.3
        seq = [[0,0], [1/frequency/2,V]]
        stream, scanRate = self.labjack.sequence2stream(seq, 1/frequency, 1)
        self.labjack.stream_out([0], stream, scanRate, loop = True)
