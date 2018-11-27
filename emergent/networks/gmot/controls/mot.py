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
        self.labjack = LabJack(devid='470017907', name='labjack')
        self.labjack.prepare_streamburst(channel=0)
        self.labjack.AOut(3,-5,HV=True)
        self.labjack.AOut(2,5, HV=True)
        self.trigger_labjack = LabJack(devid='440010734', name = 'trigger', parent=self)
        self.set_offset(0)

    def set_offset(self, offset):
        self.offset = offset
        self.trigger_labjack.AOut(1,offset)

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
<<<<<<< HEAD
    def probe_switch(self, state, params = {'stream step': 0.001, 'loading time': 1, 'probe delay': 0.0005, 'probe time': 0.1, 'trigger delay': 0.01}):
=======
    def probe_switch(self, state, params = {'loading time': 1, 'probe delay': 0.0005, 'probe time': 0.1, 'trigger delay': 0.01}):
>>>>>>> 188d6f22ffc5957779f73e116cf2e91047321910
        ''' Queue triggered stream-out on intensity servo channels '''
        if 'servo' in state:
            state['servo']['V0'] = 0
        self.actuate(state)

        cycle_time = params['loading time'] + params['probe time']
        servo = self.children['servo']
        lj = servo.labjack
<<<<<<< HEAD
        max_samples = int(cycle_time/params['stream step'])
=======
>>>>>>> 188d6f22ffc5957779f73e116cf2e91047321910

        t = np.linspace(0,cycle_time, 1000)
        y = np.zeros((len(t),2))
        y[t<params['loading time'], 0] = 3.3
        y[t>params['loading time']+params['probe delay'], 1] = 3.3
        lj.prepare_stream_out(trigger=0)
<<<<<<< HEAD
        sequence, scanRate = lj.resample(y, cycle_time, max_samples = max_samples)
=======
        sequence, scanRate = lj.resample(y, cycle_time)
>>>>>>> 188d6f22ffc5957779f73e116cf2e91047321910
        lj.stream_out([0,1], sequence, scanRate, loop=0)

        ''' Queue triggered stream-in on self.labjack '''
        self.timer.log('Preparing input stream')
        if self.labjack.stream_mode is not 'in-triggered':
            self.labjack.prepare_streamburst(0, trigger=0)
        self.process_manager._run_thread(self.probe_trigger, args=(params['trigger delay'],), stoppable=False)
        self.timer.log('Running input stream')
        data = self.labjack.streamburst(cycle_time)

        time_per_point = cycle_time/len(data)
        probe_point = int((params['loading time']+params['probe delay'])/time_per_point)
        data = data[probe_point::]
        print(np.max(data))

        return -np.max(data)

    #
    # @experiment
    # def probe_pulse(self, state, params = {'loading time': 1, 'probe time': 0.1, 'trigger delay': 0.01}):
    #     ''' Queue triggered stream-out on intensity servo channels '''
    #     self.actuate(state)
    #     cycle_time = params['loading time'] + params['probe time']
    #     servo = self.children['servo']
    #
    #     probe_labjack = servo.labjack[0]
    #     probe_stream = np.array([[0,0], [params['loading time'], self.state['servo']['V0']]])
    #     probe_labjack.prepare_stream_out(trigger=0)
    #     sequence, scanRate = probe_labjack.resample(probe_stream, cycle_time)
    #     probe_labjack.stream_out([0], sequence, scanRate, loop=0)
    #
    #     trap_labjack = servo.labjack[1]
    #     t = np.linspace(0,cycle_time, 1000)
    #     y = np.zeros((len(t),2))
    #     y[t<params['loading time'], 0] = self.state['servo']['V2']
    #     y[t<params['loading time'], 1] = self.state['servo']['V3']
    #     trap_labjack.prepare_stream_out(trigger=0)
    #     sequence, scanRate = trap_labjack.resample(y, cycle_time)
    #     trap_labjack.stream_out([0,1], sequence, scanRate, loop=0)
    #
    #     ''' Queue triggered stream-in on self.labjack '''
    #     if self.labjack.stream_mode is not 'in-triggered':
    #         self.labjack.prepare_streamburst(0, trigger=0)
    #     self.process_manager._run_thread(self.probe_trigger, args=(params['trigger delay'],), stoppable=False)
    #     data = self.labjack.streamburst(cycle_time)
    #     print(np.max(data))
    #     plt.plot(data)
    #     self.actuate(state)
    #     return -np.max(data)
    #
    # @experiment
    # def pulsed_slowing(self, state = None, params = {'pulse time': 0.5, 'settling time': 0.05}):
    #     if state is not None:
    #         self.actuate(state)
    #     self.children['servo'].lock(2,0)
    #     self.labjack.DOut(4,0)
    #     low = self.labjack.streamburst(duration=params['pulse time'], operation = 'mean')
    #     self.labjack.DOut(4,1)
    #     self.children['servo'].lock(2,1)
    #     high = self.labjack.streamburst(duration=params['pulse time'], operation = 'mean')
    #     return -high    # low is subtracted out by SRS

    @experiment
    def fluorescence(self, state, params = {'settling time': 0.1, 'duration': 0.25}):
        self.actuate(state)
        time.sleep(params['settling time'])
        data = self.labjack.streamburst(duration=params['duration'], operation = None)
        print(str(np.mean(data)) + '+/-' + str(np.std(data)))
        return -np.mean(data)

<<<<<<< HEAD
    def probe_trigger(self, trigger_delay = 0.001):
=======
    def probe_trigger(self, delay = 1):
        time.sleep(delay)
>>>>>>> 188d6f22ffc5957779f73e116cf2e91047321910
        for i in range(10):
            time.sleep(trigger_delay)
            self.trigger_labjack.DOut(4, i%2)
