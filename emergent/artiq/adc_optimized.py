from artiq.experiment import *
import pandas as pd
import numpy as np
from artiq.coredevice.sampler import adc_mu_to_volt
def prepare_data_sets(times, n_samples) -> TList(TList(TInt32)):
    return [[[0]*8]*n_samples[i] for i in range(len(times))]

class Sequencer(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("scheduler")
        self.setattr_device("core_dma")
        self.setattr_device('sampler0')         # 8 channel ADC
        self.setattr_device('ttl6')

    @kernel
    def initialize_kernel(self):
        self.core.reset()
        self.core.break_realtime()
        self.sampler0.init()
        self.core.break_realtime()
        delay(100*us)


    @kernel
    def slack(self):
        return now_mu()-self.core.get_rtio_counter_mu()

    def run(self):
        self.initialize_kernel()

        adc_channels = [0, 1, 2, 3, 4, 5, 6, 7]
        times = [10e-3, 5e-3, 10e-3]
        adc_table = [[1], [1], [1]]

        ''' Compute number of samples for each run '''
        delay = 100*us
        N_samples = []
        for time in times:
            N_samples.append(int(time/delay))
        self.data = prepare_data_sets(times, N_samples)
        slack = self.adc(times, adc_table, delay, N_samples)
        print('adc slack:', slack)
        # print(self.data)

        df = pd.DataFrame(columns=range(8))
        total_time = 0
        for i in range(len(times)):
            t0 = total_time
            for j in range(len(self.data[i])):
                d = np.atleast_2d(self.data[i][j])
                subdf = pd.DataFrame(d, index=[t0], columns = range(8))
                t0 += delay
                df = df.append(subdf)

            total_time += times[i]
        df = adc_mu_to_volt(df)
        print(df)


    @kernel
    def adc(self, times, table, delay, N_samples):
        self.core.break_realtime()
        step_number = 0
        for time in times:
            n_samples = N_samples[step_number]
            if 1 in table[step_number]:
                self.get_samples(step_number, n_samples, delay)
            step_number += 1
        return self.slack()


    @kernel
    def get_samples(self, step_number, n, dt):
        self.ttl6.on()
        for i in range(n):
            with parallel:
                self.sampler0.sample_mu(self.data[step_number][i])
                delay(dt)
        self.ttl6.off()
