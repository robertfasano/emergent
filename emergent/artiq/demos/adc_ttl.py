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


        print('Starting experiment')

        ''' Get and prepare sequence '''
        times = [100e-3, 20e-3, 15e-3]
        ttl_table = [ [1, 0, 0, 0, 0, 0, 0, 0],
                      [1, 0, 0, 0, 0, 0, 0, 0],
                      [1, 0, 0, 0, 0, 0, 0, 0]]
        ttl_table = list(map(list, zip(*ttl_table)))            # transpose
        self.set_ttl_table(ttls, ttl_channels, times, ttl_table)

        adc_table = [0, 1, 1]
        adc_delay = 100*us
        N_samples = []
        for time in times:
            N_samples.append(int(time/adc_delay))
        self.data = prepare_data_sets(times, N_samples)
        print('times:', times)
        print('ttl_table:', ttl_table)
        print('adc_table:', adc_table)
        self.execute(times, ttls, ttl_channels, ttl_table, adc_table, adc_delay, N_samples)


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
                with sequential:
                    if adc_table[col] == 1:
                        self.get_samples(col, N_samples[col], adc_delay)
                    else:
                        delay(time)
            col += 1

        print('sequence done')

    @kernel
    def adc(self, times, table, adc_delay, N_samples):
        step_number = 0
        for time in times:
            n_samples = N_samples[step_number]
            # if 1 in table[step_number]:
            if table[step_number] == 1:
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
