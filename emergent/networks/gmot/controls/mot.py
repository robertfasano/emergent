from emergent.archetypes import Control
import time
from utility import experiment
from scipy.stats import linregress
from scipy.optimize import curve_fit
import numpy as np
from emergent.archetypes.parallel import ProcessHandler
from emergent.devices.labjack import LabJack
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
        self.TTL_labjack = LabJack(devid='470016970', name = 'TTL')
        self.trigger_labjack = LabJack(devid='440010734', name='trigger')
        self.timer = Timer()
        self.MEMS_enable(1)

    def MEMS_enable(self, state):
        self.TTL_labjack.DOut(3, state)

    def MEMS_wave(self, period):
        t = np.linspace(0,period, 100000)
        y = np.zeros(len(t))
        y[t>period/2] = 1
        y = self.TTL_labjack.array_to_bitmask(np.atleast_2d(y).T, [3])
        self.TTL_labjack.prepare_stream_out(trigger=None)
        sequence, scanRate = self.TTL_labjack.resample(np.atleast_2d(y).T, period)
        self.TTL_labjack.stream_out(['FIO_STATE'], sequence, scanRate, loop=1)

    @experiment
    def probe_switch(self, state, params = {'samples': 1, 'trigger delay': 0.1, 'stream step': 0.001}):
        results = []
        self.TTL_labjack.DIO_STATE([1,2,3], [1,0,1])        # switch off light and integrators
        self.actuate(state)

        for key in ['loading time', 'probe time', 'probe delay', 'gate time']:
            params[key] = self.children['loader'].state[key]/1000
        cycle_time = params['loading time'] + params['probe time']
        max_samples = int(cycle_time/params['stream step'])

        ''' Prepare TTL stream '''
        self.TTL_labjack.prepare_digital_stream([1,2,3,4])

        ''' Prepare TTL pattern '''
        t = np.linspace(0,cycle_time, 100000)
        y = np.zeros((len(t),4))
        y[t<params['loading time'], 1] = 1          # TTL high shuts off probe RF switch (FIO2)
        y[t<params['loading time'], 2] = 1          # TTL high to enable MOT MEMS (FIO3)
        y[t<params['loading time'], 3] = 0          # TTL low to enable MOT integrators (FIO4)

        y[t>params['loading time'], 2] = 0          # TTL low to disable MOT MEMS (FIO3)
        y[t>params['loading time'], 3] = 1          # TTL high to disable MOT integrators and start reading (FIO4)

        y[t>params['loading time']-params['probe delay'], 1] = 0    # TTL low to turn on probe RF switch/integrator (FIO2)
        y[t>params['loading time']-params['probe delay'], 0] = 1    # TTL high to start acquisition (FIO1)
        y = self.TTL_labjack.array_to_bitmask(y, [1,2,3,4])



        for i in range(params['samples']):
            self.TTL_labjack.DIO_STATE([1,2,3], [1,0,1])        # switch off light and integrators

            ''' Write TTL pattern '''
            self.TTL_labjack.prepare_stream_out(trigger=0)
            sequence, scanRate = self.TTL_labjack.resample(np.atleast_2d(y).T, cycle_time)
            self.TTL_labjack.stream_out(['FIO_STATE'], sequence, scanRate, loop=0)

            ''' Queue triggered stream-in on self.labjack '''
            if self.labjack.stream_mode is not 'in-triggered':
                self.labjack.prepare_streamburst(0, trigger=0)
            self.process_manager._run_thread(self.probe_trigger, args=(params['trigger delay'],), stoppable=False)
            data = np.array(self.labjack.streamburst(params['probe time']))

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

    # def probe_trigger(self, trigger_delay = 0.001):
    #     for i in range(10):
    #         time.sleep(trigger_delay)
    #         self.trigger_labjack.DOut(4, i%2)

    def probe_trigger(self, trigger_delay = 0.001):
        for i in range(10):
            time.sleep(trigger_delay)
            self.trigger_labjack.AOut(0, 3.3*(i%2))
