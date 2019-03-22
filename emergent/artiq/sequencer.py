from artiq.experiment import *
import numpy as np
import math
import requests
import time
from flask import Flask
from flask_socketio import SocketIO, emit
import logging

HUB = 'hub'
LIVE = True



def get_time() -> TFloat:
    return time.time()

def get_read_times() -> TList(TList(TFloat)):
    ''' Returns a list of lists like [[tstart, tend, dt]] '''
    reads = requests.get('http://127.0.0.1:5000/artiq/run').json()['adc']
    times = []
    for r in reads:
        times.append([float(r['start']), float(r['end']), float(r['step'])])
    return times

def get_read_channels() -> TList(TList(TInt32)):
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

def get_ttl_times() -> TList(TFloat):
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
        @self.socketio.on('submit')
        def submit():
            print('Received submit')
            self._submit_emergent = 1

        ''' post handshake to start connection '''
        from threading import Thread
        thread = Thread(target=self.socketio.run, args=(app,), kwargs={'port': 54031})
        thread.start()
        print('Starting socket connection')
        requests.post('http://127.0.0.1:5000/artiq/handshake', json={'port': 54031})


    def store_adc_reads(self, data):
        data = list(map(list, zip(*data)))

        self.adc_reads.append(data)

    def post_adc_data(self):
        post_samples(self.adc_reads)

    def process_submitted(self) -> TBool:
        return bool(self._submit_emergent)

    def reset_process(self):
        self._submit_emergent = 0

    def reset_adc_reads(self):
        self.adc_reads = []

    @kernel
    def run(self):
        self.core.reset()
        self.sampler0.init()

        ttls = self._ttls

        ttl_channels = [4, 5]

        if not LIVE:
            times = get_ttl_times()
            table = get_ttl_states(ttl_channels)
            self.set_ttl_table(ttls, ttl_channels, times, table)

        while True:
            ''' Check if EMERGENT has submitted a process '''
            if not self.process_submitted():
                continue
            self.reset_process()
            self.reset_adc_reads()

            print('Starting experiment')
            pid = get_pid()
            n_samples = 3
            time_between_samples = 15*us
            ''' Read ADC '''

            if LIVE:
                ''' Get and prepare TTL state '''
                times = get_ttl_times()
                table = get_ttl_states(ttl_channels)
                self.set_ttl_table(ttls, ttl_channels, times, table)

                ''' Get ADC reads '''
                adc_times = get_read_times()
                adc_channels = get_read_channels()

                self.core.break_realtime()
                with parallel:
                    # self.TTL_playback()
                    # self.get_raw_samples(n_samples, time_between_samples, pid)
                    self.perform_adc_reads(adc_times, adc_channels)
                self.core.wait_until_mu(now_mu())       # wait until hardware cursor reaches time cursor. Important!!
                self.post_adc_data()

            else:
                self.TTL_playback()
                self.core.wait_until_mu(now_mu())

    @kernel
    def perform_adc_reads(self, adc_times, adc_channels):
        for i in range(len(adc_times)):
            lst = adc_times[i]
            start = lst[0]
            end = lst[1]
            step = lst[2]
            n_samples = int((end-start)/step)
            delay(start*s)
            self.get_raw_samples(n_samples, step, adc_channels[i])


    @kernel
    def get_raw_samples(self, n_samples, time_between_samples, channels):

        raw_samples = [[0.0]*8 for i in range(n_samples)]
        i=0
        with sequential:
            self.ttl6.on()
            for i in range(n_samples):
                with parallel:
                    self.sampler0.sample(raw_samples[i])
                    delay(time_between_samples*s)

        self.ttl6.off()

        # filter by channels
        for i in range(len(raw_samples)):
            raw_samples[i] = [raw_samples[i][j] for j in channels]
        # raw_samples = self.core.sampler.adc_mu_to_volt(raw_samples)
        self.store_adc_reads(raw_samples)

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
