from artiq.experiment import *
import numpy as np
import math
import requests
import time
from flask import Flask
from flask_socketio import SocketIO, emit
import logging


def prepare_sample_sets(times) -> TList(TList):
    x = []
    for t in times:
        x.append([])
    return x

def prepare_data_array(times, adc_table) -> TList(TList(TInt32)):
    ''' Determine total sampling time and prepare data array '''
    total_time = 0.0
    col = 0
    data = []
    for time in times:
        if 1 in adc_table[col]:
            total_time += time
            samples = int(1.5e6*time) - int(1.5e6*time)%8
            data.append([0]*samples)
        col += 1
    return data

def get_time() -> TFloat:
    return time.time()

def get_read_times() -> TList(TList(TFloat)):
    ''' Returns a list of lists like [[tstart, tend, dt]] '''
    reads = requests.get('http://127.0.0.1:5000/artiq/run').json()['adc']
    times = []
    for r in reads:
        times.append([float(r['start']), float(r['end']), float(r['step'])])
    return times

def get_adcs() -> TList(TList(TInt32)):
    ''' Returns a list of lists like [[0], [1,2]] '''
    reads = requests.get('http://127.0.0.1:5000/artiq/run').json()['adc']
    channel_sets = []
    for r in reads:
        channel_sets.append(r['channels'])
    return channel_sets

def post_samples(samples):
    print('sending data')
    for i in range(len(samples)):
        for j in range(len(samples[i])):
            samples[i][j] = [int(x) for x in samples[i][j]]
    requests.post('http://127.0.0.1:5000/artiq/run', json={'result': samples})

def get_pid() -> TStr:
    return requests.get('http://127.0.0.1:5000/artiq/run').json()['pid']

def get_ttls(ttl_channels) -> TList(TList(TInt32)):
    ''' Queries the EMERGENT API and receives a sequence of the format
            [{'name': 'step1', 'TTL': [0,1], 'ADC': [0]}]
        Prepares a TTL table from this sequence. '''
    sequence = requests.get('http://127.0.0.1:5000/artiq/run').json()['sequence']
    state = []
    for step in sequence:
        step_state = []
        for ch in ttl_channels:
            if ch in step['TTL'] or str(ch) in step['TTL']:
                step_state.append(1)
            else:
                step_state.append(0)
        state.append(step_state)
    state = list(map(list, zip(*state)))            # transpose

    return state

def get_adcs(adc_channels) -> TList(TList(TInt32)):
    ''' Queries the EMERGENT API and receives a sequence of the format
            [{'name': 'step1', 'TTL': [0,1], 'ADC': [0]}]
        Prepares an ADC table from this sequence. '''
    sequence = requests.get('http://127.0.0.1:5000/artiq/run').json()['sequence']
    state = []
    for step in sequence:
        step_state = []
        for ch in adc_channels:
            if ch in step['ADC'] or str(ch) in step['ADC']:
                step_state.append(1)
            else:
                step_state.append(0)
        state.append(step_state)
    # state = list(map(list, zip(*state)))            # transpose

    return state


def get_ttl_states(ttl_channels) -> TList(TList(TInt32)):
    ttl_channels.sort()
    run = requests.get('http://127.0.0.1:5000/artiq/run').json()
    sequence = run['sequence']
    switches = requests.get('http://127.0.0.1:5000/hubs/%s/switches/ttl'%HUB).json()
    state = []
    for step in sequence:
        step_state = []
        for ch in ttl_channels:
            switch_name = switches[str(ch)]['name']
            step_state.append(step['state'][switch_name])
        # state.append(list(step['state'].values()))
        state.append(step_state)
    state = list(map(list, zip(*state)))            # transpose
    return state

def get_timesteps() -> TList(TFloat):
    run = requests.get('http://127.0.0.1:5000/artiq/run').json()
    sequence = run['sequence']

    times = []
    for step in sequence:
        times.append(float(step['duration']))
    return times

class Sequencer(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("scheduler")
        self.setattr_device("core_dma")

        self._ttls = []
        for i in range(8):
            self.setattr_device("ttl%i"%i)
            dev = getattr(self, "ttl%i"%i)
            self._ttls.append(dev)

        self.setattr_device('zotino0')          # 32 channel DAC
        self.setattr_device('sampler0')         # 8 channel ADC

        logging.getLogger('socketio').setLevel(logging.ERROR)
        logging.getLogger('engineio').setLevel(logging.ERROR)
        app = Flask(__name__)
        self.socketio = SocketIO(app, logger=False, port=54031)
        #
        #
        self._submit_emergent = 0
        @self.socketio.on('submit')
        def submit():
            print('Received submit')
            self._submit_emergent = 1
        #
        ''' post handshake to start connection '''
        from threading import Thread
        thread = Thread(target=self.socketio.run, args=(app,), kwargs={'port': 54031})
        thread.start()
        print('Starting socket connection')
        requests.post('http://127.0.0.1:5000/artiq/handshake', json={'port': 54031})

        self.data = []


    ''' Acquired data handling '''
    @rpc(flags={"async"})
    def store_adc_reads(self, data):
        # data = list(map(list, zip(*data)))

        self.adc_reads.append(data)

    def post_adc_data(self):
        post_samples(self.adc_reads)

    def reset_adc_reads(self):
        self.adc_reads = []


    ''' Start management '''
    def process_submitted(self) -> TBool:
        return bool(self._submit_emergent)

    def reset_process(self):
        self._submit_emergent = 0



    @kernel
    def initialize_kernel(self):
        self.core.reset()
        self.core.break_realtime()
        self.sampler0.init()
        self.core.break_realtime()
        delay(100*us)

    @kernel
    def slack(self):
        print(now_mu()-self.core.get_rtio_counter_mu())

    def run(self):
        self.initialize_kernel()
        ttls = self._ttls

        ttl_channels = [0, 1, 2, 3, 4, 5, 6, 7]
        adc_channels = [0, 1, 2, 3, 4, 5, 6, 7]


        while True:
            ''' Check if EMERGENT has submitted a process '''
            if not self.process_submitted():
                continue
            self.reset_process()
            # self.reset_adc_reads()

            print('Starting experiment')

            ''' Get and prepare TTL state '''
            times = get_timesteps()
            ttl_table = get_ttls(ttl_channels)
            #
            # ''' Get ADC reads '''
            adc_table = get_adcs(adc_channels)

            sample_sets = prepare_sample_sets(times)
            def set_results(x, i):
                nonlocal sample_sets
                sample_sets[i] = x


            self.set_ttl_table(ttls, ttl_channels, times, ttl_table)

            # self.core.break_realtime()
            # self.slack()
            # with parallel:
                # self.TTL_playback()

            self.execute(times, ttl_table, adc_table, set_results)
            # self.execute_adc_pattern(self.sampler0, adc_channels, times, adc_table, set_results)
            print(sample_sets)
                # self.perform_adc_reads(adc_times, adc_channels)
            self.core.wait_until_mu(now_mu())       # wait until hardware cursor reaches time cursor. Important!!
            # self.post_adc_data()



    @kernel(flags={"fast-math"})
    def execute(self, times, ttl_table, adc_table, set_results):
        self.core.break_realtime()
        with parallel:
            # self.execute_adc_pattern(self.sampler0, set_results, times, adc_table)
            self.execute_adc_pattern_test(self.sampler0, set_results, times, adc_table)

            self.TTL_playback()

    @kernel
    def execute_adc_pattern_test(self, sampler, rpc, times, adc_table):
        dt = 30*ms
        n = int(dt*1.5e6)-int(dt*1.5e6)%8
        # raw_samples = [[0]*8 for i in range(n)]
        raw_samples = [0]*(8*n)
        delay(100*ms)
        for i in range(n):
            with parallel:
                sampler.sample_mu(raw_samples[i])
                delay(200*us)
        rpc(raw_samples, 0)


    @kernel(flags={"fast-math"})
    def get_dt(self, time, n):
        if n == 1:
            return time-100*us           # need to compensate for calculation time!!
        else:
            return time/(n-1)-100/n*us

    @kernel(flags={"fast-math"})
    def execute_adc_pattern(self, sampler, rpc, times, table):
        # self.get_samples(sampler, rpc)
        n = 15
        col = 0
        for time in times:
            delay(100*us)            # compensate for calculation time
            dt = self.get_dt(time, n)

            with parallel:
                if 1 in table[col]:
                    self.get_samples(sampler, rpc, col)
            col += 1

    @kernel(flags={"fast-math"})
    def get_samples(self, sampler, rpc, col, n, dt):
        data = [[0]*8 for i in range(n)]
        for i in range(n):
            with parallel:
                sampler.sample_mu(data[i])
                delay(dt)
        rpc(data, col)

    @kernel
    def set_ttl_table_craig(self, ttls, channels, times, table):
        with self.core_dma.record("table"):
            col=0
            for time in times:
                delay(time*.1)
                with parallel:
                    with sequential:
                        delay(time*0.9)
                        row=0
                        for ch in channels:
                            self.set_ttl(ttls[ch], table[row][col])
                            row = row + 1
                col = col + 1

    @kernel
    def execute_ttl_pattern(self, ttls, channels, times, table):
        col=0
        for time in times:
            start_mu = now_mu()
            with parallel:
                row=0
                for ch in channels:
                    at_mu(start_mu)
                    if table[row][col]==1:
                        ttls[ch].pulse(time)
                    else:
                        delay(time)
                    row = row + 1
                col = col + 1

    @kernel
    def set_ttl_table(self, ttls, channels, times, table):
        with self.core_dma.record("table"):
            self.execute_ttl_pattern(ttls, channels, times, table)

    @kernel
    def TTL_playback(self):
        h_table = self.core_dma.get_handle("table")
        self.core.break_realtime()
        self.core_dma.playback_handle(h_table)
        self.core_dma.erase("table")
