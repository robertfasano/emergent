from artiq.experiment import *

def prepare_sample_sets(times) -> TList(TList):
    x = []
    for t in times:
        x.append([])
    return x

def prepare_data_sets(times, n_samples) -> TList(TList(TInt32)):
    x = []
    i=0
    for t in times:
        x.append([[0]*8]*n_samples[i])
        i += 1
    return x

class Sequencer(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("scheduler")
        self.setattr_device("core_dma")
        self.setattr_device('sampler0')         # 8 channel ADC
        self.data = []

    @rpc(flags={"async"})
    def append_data(self, x, i):
        self.data.append(x)

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

        ''' Compute actual read times. Example: let times = [1, 0.5, 1] and
            adc_table = [[1], [0], [1]]. This means we should read for 1s, wait
            for 0.5s, and read for 1s. '''
        read_times = []
        wait_times = []
        for i in range(len(times)):
            if 1 in adc_table[i]:
                read_times.append(times[i])
                wait_times.append(0.0)
            else:
                read_times.append(0.0)
                wait_times.append(times[i])

        ''' Compute number of samples for each run '''
        fixed_delay = 100*us
        N_samples = []
        for time in times:
            N_samples.append(int(time/fixed_delay))
        self.data = prepare_data_sets(times, N_samples)

        # self.sample_sets = prepare_sample_sets(times)
        def set_results(x, i):
            nonlocal sample_sets
            sample_sets[i] = x


        ''' Two different paths to ADC generation:
            1. Acquire one sample, RPC to host, and repeat
            2. Stream and decimate (may not work for longer measurements)

            Main problem with #1 is dynamic delay time calculation actually eating
            time that we could be measuring. Solution: define a fixed sampling rate
            which is long enough to accommodate an RPC.

            Second problem: defining an ADC table and checking if we should be reading
            adds more load to the kernel than necessary; we could speed this up by
            computing read times in the non-deterministic part of the code (before the
            kernel methods are called).


            The following methods benchmark various ADC generation routes:
            1. adc_fixed_delay: make repeated reads filling up a time interval
                                with a defined delay. RPC data to host after.
                                Checking against adc_table done in function.
            2. adc_fixed_delay_logic_optimized: same as adc_fixed_delay, but with adc_table
                                                parsing done before the kernel part.
            3. adc_fixed_delay_samples_optimized: same as adc_fixed_delay, but with n_samples
                                                  determined before the kernel part.
            4. adc_fixed_delay_optimized: combining logic and samples optimizations to minimize
                                          kernel calculations
            5. adc_fixed_delay_optimized_async: same as #4, but with an async RPC call

            **** RESULTS ****
            adc_fixed_delay_samples_optimized: 109736
            adc_fixed_delay: 6011624
            adc_fixed_delay_logic_optimized: 5931304
            adc_fixed_delay_optimized: 5877776
            adc_fixed_delay_optimized_async: 9519944

            The optimizations actually decrease performance except for
            the asynchronous RPC.
        '''
        # sample_sets = prepare_sample_sets(times)
        # slack = self.adc_fixed_delay_samples_optimized(self.sampler0, set_results, read_times, wait_times, fixed_delay, N_samples)
        # print('adc_fixed_delay_samples_optimized:', slack)
        #
        #
        # sample_sets = prepare_sample_sets(times)
        # slack = self.adc_fixed_delay(self.sampler0, set_results, times, adc_table, fixed_delay)
        # print('adc_fixed_delay:', slack)
        #
        sample_sets = prepare_sample_sets(times)
        # self.data = prepare_sample_sets(times)
        slack = self.adc_fixed_delay_async(self.sampler0, set_results, times, adc_table, fixed_delay)
        print('adc_fixed_delay_async:', slack)
        print(self.data)
        # sample_sets = prepare_sample_sets(times)
        # slack = self.adc_fixed_delay_logic_optimized(self.sampler0, set_results, read_times, wait_times, fixed_delay)
        # print('adc_fixed_delay_logic_optimized:', slack)
        #
        #
        # sample_sets = prepare_sample_sets(times)
        # slack = self.adc_fixed_delay_optimized(self.sampler0, set_results, read_times, wait_times, fixed_delay, N_samples)
        # print('adc_fixed_delay_optimized:', slack)
        #
        # sample_sets = prepare_sample_sets(times)
        # slack = self.adc_fixed_delay_optimized_async(self.sampler0, read_times, wait_times, fixed_delay, N_samples)
        # print('adc_fixed_delay_optimized_async:', slack)
        #
        # sample_sets = prepare_sample_sets(times)
        # slack = self.adc_fast_sampling(self.sampler0, fixed_delay)
        # print('adc_fast_sampling:', slack)

    @kernel(flags={"fast-math"})
    def adc_fixed_delay(self, sampler, rpc, times, table, fixed_delay):
        self.core.break_realtime()
        col = 0
        for time in times:
            n_samples = int(time/fixed_delay)
            if 1 in table[col]:
                self.get_samples(sampler, rpc, col, n_samples, fixed_delay)
            col += 1
        return self.slack()

    @kernel(flags={"fast-math"})
    def adc_fast_sampling(self, sampler, fixed_delay):
        self.core.break_realtime()
        col = 0
        n_samples = 50
        self.get_samples(sampler, self.append_data, col, n_samples, fixed_delay)
        col += 1
        return self.slack()

    @kernel(flags={"fast-math"})
    def adc_fixed_delay_async(self, sampler, rpc, times, table, fixed_delay):
        self.core.break_realtime()
        col = 0
        for time in times:
            n_samples = int(time/fixed_delay)
            if 1 in table[col]:
                self.get_samples(sampler, self.append_data, col, n_samples, fixed_delay)
            col += 1
        return self.slack()

    @kernel(flags={"fast-math"})
    def adc_fixed_delay_logic_optimized(self, sampler, rpc, read_times, wait_times, fixed_delay):
        self.core.break_realtime()
        for i in range(len(read_times)):
            if read_times[i] > 0:
                n_samples = int(read_times[i]/fixed_delay)
                self.get_samples(sampler, rpc, i, n_samples, fixed_delay)
            else:
                delay(wait_times[i])
        return self.slack()

    @kernel(flags={"fast-math"})
    def adc_fixed_delay_samples_optimized(self, sampler, rpc, times, table, fixed_delay, N_samples):
        self.core.break_realtime()
        col = 0
        for time in times:
            if table[col] == 1:
                self.get_samples(sampler, rpc, col, N_samples[col], fixed_delay)
            col += 1
        return self.slack()

    @kernel(flags={"fast-math"})
    def adc_fixed_delay_optimized(self, sampler, rpc, read_times, wait_times, fixed_delay, N_samples):
        self.core.break_realtime()
        for i in range(len(read_times)):
            if read_times[i] > 0:
                self.get_samples(sampler, rpc, i, N_samples[i], fixed_delay)
            else:
                delay(wait_times[i])
        return self.slack()

    @kernel(flags={"fast-math"})
    def adc_fixed_delay_optimized_async(self, sampler, read_times, wait_times, fixed_delay, N_samples):
        self.core.break_realtime()
        for i in range(len(read_times)):
            if read_times[i] > 0:
                self.get_samples(sampler, self.append_data, i, N_samples[i], fixed_delay)
            else:
                delay(wait_times[i])
        return self.slack()

    @kernel(flags={"fast-math"})
    def get_samples(self, sampler, rpc, col, n, dt):
        # data = [[0]*8 for i in range(n)]
        for i in range(n):
            with parallel:
                # sampler.sample_mu(data[i])
                start_index = int(8*i)
                end_index = int(8*(1+i))
                sampler.sample_mu(self.data[col][i])

                delay(dt)
        # rpc(data, col)
