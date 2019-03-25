from artiq.experiment import *
import numpy as np
import requests
from flask import Flask
from flask_socketio import SocketIO, emit
import logging
import pandas as pd
from artiq.coredevice.sampler import adc_mu_to_volt


def prepare_data_sets(times, n_samples) -> TList(TList(TInt32)):
    return [[[0]*8]*n_samples[i] for i in range(len(times))]

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

def post_results(samples):
    print('sending data')
    # for i in range(len(samples)):
    #     for j in range(len(samples[i])):
    #         samples[i][j] = [int(x) for x in samples[i][j]]
    requests.post('http://127.0.0.1:5000/artiq/run', json={'result': samples.to_json()})

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

        self._submit_emergent = 0
        self.do_adc = 0
        @self.socketio.on('submit')
        def submit():
            self._submit_emergent = 1
            self.do_adc = 1

        @self.socketio.on('hold')
        def submit():
            self._submit_emergent = 1

        ''' post handshake to start connection '''
        from threading import Thread
        thread = Thread(target=self.socketio.run, args=(app,), kwargs={'port': 54031})
        thread.start()
        print('Starting socket connection')
        requests.post('http://127.0.0.1:5000/artiq/handshake', json={'port': 54031})

    ''' Start management '''
    def process_submitted(self) -> TBool:
        return bool(self._submit_emergent)

    def reset_process(self):
        self._submit_emergent = 0
        self.do_adc = 0

    @kernel
    def initialize_kernel(self):
        self.core.reset()
        self.core.break_realtime()
        self.sampler0.init()
        self.core.break_realtime()
        delay(1*ms)

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

            print('Starting experiment')

            ''' Get and prepare sequence '''
            times = get_timesteps()
            ttl_table = get_ttls(ttl_channels)
            self.set_ttl_table(ttls, ttl_channels, times, ttl_table)

            adc_table = get_adcs(adc_channels)
            adc_delay = 1*ms
            N_samples = []
            for time in times:
                N_samples.append(int(time/adc_delay))

            self.data = [[[0]]]
            if self.do_adc == 1:
                self.data = prepare_data_sets(times, N_samples)

            self.execute(times, ttls, ttl_channels, ttl_table, adc_table, adc_delay,  N_samples)

            if self.do_adc == 1:
                df = pd.DataFrame(columns=range(8))
                total_time = 0
                for i in range(len(times)):
                    t0 = total_time
                    for j in range(len(self.data[i])):
                        d = np.atleast_2d(self.data[i][j])
                        subdf = pd.DataFrame(d, index=[t0], columns = range(8))
                        t0 += adc_delay
                        df = df.append(subdf)

                    total_time += times[i]
                df = adc_mu_to_volt(df)
                print('converted')
                post_results(df)

            self.reset_process()

    @kernel
    def execute(self, times, ttls, ttl_channels, ttl_table, adc_table, adc_delay, N_samples):
        self.core.break_realtime()
        delay(50*ms)            # adjust as needed to avoid RTIO underflows

        col = 0
        for time in times:
            start_mu = now_mu()
            with parallel:
                ''' TTL '''
                with sequential:
                    row=0
                    for ch in ttl_channels:
                        at_mu(start_mu)
                        if ttl_table[row][col]==1:
                            # ttls[ch].pulse(time)
                            ttls[ch].on()
                            delay(time)
                        else:
                            ttls[ch].off()
                            delay(time)
                        row = row + 1

                ''' ADC '''
                if self.do_adc == 1:
                    with sequential:
                        if 1 in adc_table[col]:
                            self.get_samples(col, N_samples[col], adc_delay)
                        else:
                            delay(time)
            col += 1

    @kernel
    def adc(self, times, table, adc_delay, N_samples):
        delay(1*ms)
        step_number = 0
        for time in times:
            n_samples = N_samples[step_number]
            if 1 in table[step_number]:
                self.get_samples(step_number, n_samples, adc_delay)
            else:
                delay(time)
                print('delay')
            step_number += 1
        # return self.slack()

    @kernel
    def get_samples(self, step_number, n, dt):
        # print('get step', step_number, 'then wait', dt, 'for', n)
        for i in range(n):
            with parallel:
                with sequential:
                    self.sampler0.sample_mu(self.data[step_number][i])
                delay(dt)
            # print(self.data[0])


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
                        # ttls[ch].pulse(time)
                        ttls[ch].on()
                        delay(time)
                    else:
                        ttls[ch].off()
                        delay(time)
                    row = row + 1
                col = col + 1

    @kernel
    def set_ttl_table(self, ttls, channels, times, table):
        with self.core_dma.record("table"):
            self.execute_ttl_pattern(ttls, channels, times, table)

    @kernel
    def TTL_playback(self, table):
        self.core_dma.playback_handle(table)
        # self.core_dma.erase("table")
