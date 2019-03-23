from artiq.experiment import *

def prepare_sample_sets(times) -> TList(TList):
    x = []
    for t in times:
        x.append([])
    return x

class Sequencer(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("scheduler")
        self.setattr_device("core_dma")
        self.setattr_device('sampler0')         # 8 channel ADC
        self.data = []

    @rpc(flags={"async"})
    def append_data(x):
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
        times = [100e-3, 50e-3, 100e-3]
        adc_table = [[1], [0], [1]]

        ''' Compute actual read times. Example: let times = [1, 0.5, 1] and
            adc_table = [[1], [0], [1]]. This means we should read for 1s, wait
            for 0.5s, and read for 1s. '''
        read_times = []
        wait_times = []
        for i in range(len(times)):
            if 1 in adc_table[i]:
                read_times.append(times[i])
                wait_times.append(0)
            else:
                read_times.append(0)
                wait_times.append(times[i])

        ''' Compute number of samples for each run '''
        fixed_delay = 100*us
        N_samples = []
        for time in times:
            N_samples.append(int(time/fixed_delay))


        sample_sets = prepare_sample_sets(times)
        def set_results(x, i):
            nonlocal sample_sets
            sample_sets[i] = x

        self.core.break_realtime()
        self.execute_adc_pattern_test(self.sampler0, set_results, times, adc_table)

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

        '''
        self.core.break_realtime()
        slack = self.adc_fixed_delay(self.sampler0, set_results, times, adc_table, fixed_delay)
        print('adc_fixed_delay:', slack)

        self.core.break_realtime()
        slack = self.adc_fixed_delay_logic_optimized(self.sampler0, set_results, read_times, wait_times, fixed_delay)
        print('adc_fixed_delay_logic_optimized:', slack)

        self.core.break_realtime()
        slack = self.adc_fixed_delay_samples_optimized(self.sampler0, set_results, read_times, wait_times, fixed_delay, N_samples)
        print('adc_fixed_delay_samples_optimized:', slack)

        self.core.break_realtime()
        slack = self.adc_fixed_delay_optimized(self.sampler0, set_results, read_times, wait_times, fixed_delay, N_samples)
        print('adc_fixed_delay_optimized:', slack)

        self.core.break_realtime()
        slack = self.adc_fixed_delay_optimized_async(self.sampler0, set_results, read_times, wait_times, fixed_delay, N_samples)
        print('adc_fixed_delay_optimized_async:', slack)

    @kernel(flags={"fast-math"})
    def adc_fixed_delay(self, sampler, rpc, times, table, fixed_delay):
        col = 0
        for time in times:
            n_samples = int(time/fixed_delay)
            if 1 in table[col]:
                self.get_samples(sampler, rpc, col, n_samples, fixed_delay)
            col += 1
        return slack()

    @kernel(flags={"fast-math"})
    def adc_fixed_delay_logic_optimized(self, sampler, rpc, read_times, wait_times, fixed_delay):
        for i in range(read_times):
            if read_times[i] > 0:
                n_samples = int(read_times[i]/fixed_delay)
                self.get_samples(sampler, rpc, col, n_samples, fixed_delay)
            else:
                delay(wait_times[i])
        return slack()

    @kernel(flags={"fast-math"})
    def adc_fixed_delay_samples_optimized(self, sampler, rpc, times, table, fixed_delay, N_samples):
        col = 0
        for time in times:
            if 1 in table[col]:
                self.get_samples(sampler, rpc, col, N_samples[col], fixed_delay)
            col += 1
        return slack()

    @kernel(flags={"fast-math"})
    def adc_fixed_delay_optimized(self, sampler, rpc, read_times, wait_times, fixed_delay, N_samples):
        for i in range(read_times):
            if read_times[i] > 0:
                self.get_samples(sampler, rpc, col, N_samples[i], fixed_delay)
            else:
                delay(wait_times[i])
        return slack()

    @kernel(flags={"fast-math"})
    def adc_fixed_delay_optimized_async(self, sampler, read_times, wait_times, fixed_delay, N_samples):
        for i in range(read_times):
            if read_times[i] > 0:
                self.get_samples(sampler, self.append_data, col, N_samples[i], fixed_delay)
            else:
                delay(wait_times[i])
        return slack()

    @kernel(flags={"fast-math"})
    def get_samples(self, sampler, rpc, col, n, dt):
        data = [[0]*8 for i in range(n)]
        for i in range(n):
            with parallel:
                sampler.sample_mu(data[i])
                delay(dt)
        rpc(data, col)
