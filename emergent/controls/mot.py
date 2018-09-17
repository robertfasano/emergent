from emergent.archetypes.node import Control
import time
from utility import cost
from scipy.stats import linregress
import numpy as np

class MOT(Control):
    def __init__(self, name, parent = None, path='.'):
        super().__init__(name, parent = parent, path=path)

    def add_labjack(self, labjack):
        self.labjack = labjack
        self.labjack.prepare_streamburst(channel=0)
        self.labjack.AOut(7,-5,HV=True)
        self.labjack.AOut(6,5, HV=True)
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

    def stream(self, period = 1, amplitude = 0.1):
        key='coils.I1'
        self.cycle_time = period
        self.inputs[key].sequence = [(0,0), (period/2, amplitude)]
        data = self.clock.prepare_stream(key)

        self.labjack.stream_out(0, data)

    @cost
    def pulsed_slowing(self, state = None):
        ''' Toggle between high and low magnetic field; measure mean fluorescence
            in both cases and return the difference. '''
        if state is not None:
            self.actuate(state)
        self.labjack.DOut(4,0)
        time.sleep(0.05)
        self.labjack.AOut(1, 0) # output DC level for subtraction with SRS
        low = self.labjack.streamburst(duration=0.05, operation = 'mean')
        self.labjack.AOut(1, low) # output DC level for subtraction with SRS
        self.labjack.DOut(4,1)
        time.sleep(0.05)
        high = self.labjack.streamburst(duration=0.05, operation = 'mean')
        return -high    # low is subtracted out by SRS

    @cost
    def pulsed_field_mean(self, state):
        ''' Toggle between high and low magnetic field; measure mean fluorescence
            in both cases and return the difference. '''
        self.actuate(state)
        self.actuate({'coils':{'I1':0, 'I2':0})
        time.sleep(0.075)
        self.labjack.AOut(1, 0) # output DC level for subtraction with SRS
        low = self.labjack.streamburst(duration=0.2, operation = 'mean')
        self.actuate({'coils':{'I1':70, 'I2':70})
        self.labjack.AOut(1, low) # output DC level for subtraction with SRS
        time.sleep(0.075)
        high = self.labjack.streamburst(duration=0.2, operation = 'mean')

        return -high    # low is subtracted out by SRS

    @cost
    def pulsed_field_slope(self, state):
        ''' Toggle between high and low magnetic field; measure mean fluorescence
            in both cases and return the difference. '''
        self.actuate(state)
        self.actuate({'coils':{'I1':0, 'I2':0})
        time.sleep(0.075)
        self.labjack.AOut(1, 0) # output DC level for subtraction with SRS
        low = self.labjack.streamburst(duration=0.2, operation = 'mean')
        self.actuate({'coils':{'I1':70, 'I2':70})
        self.labjack.AOut(1, low) # output DC level for subtraction with SRS
        time.sleep(0.075)
        # high = self.labjack.streamburst(duration=0.2, operation = 'ptp')
        data = self.labjack.streamburst(duration=0.2, operation = None)
        axis = np.linspace(0,.2,len(data))

        slope, intercept, r, p, err = linregress(axis, data)
        z = slope/err
        print('Slope:', slope, 'uncertainty:', err, 'z:',z)
        return -z    # low is subtracted out by SRS


    def wave(self, frequency=2):
        V = 3.3
        seq = [[0,0], [1/frequency/2,V]]
        stream, scanRate = self.labjack.sequence2stream(seq, 1/frequency, 1)
        self.labjack.stream_out([0], stream, scanRate, loop = True)

    def align(self, dim=2, numpoints = 10, span = 10):
        import msvcrt
        import numpy as np

        xmin = -span/2
        xmax = span/2
        ''' Form search grid '''
        grid = []
        for n in range(dim):
            space = np.linspace(xmin, xmax, numpoints)
            grid.append(space)
        grid = np.array(grid)
        points = np.transpose(np.meshgrid(*[grid[n] for n in range(dim)])).reshape(-1,dim)

        ''' Start at origin and step through points with manual actuation '''
        X = np.zeros(dim)

        for point in points:
            ''' Generate next point '''
            diff = point-X
            X = point
            ''' Give instructions to user and wait for keypress '''
            print('Next point:', X)
            instructions = ''
            for ax in range(dim):
                ax_instructions = 'Axis %i change: -%f\t'%(ax, diff[ax])
                instructions += ax_instructions
            print(instructions)
            msvcrt.getch()          # wait for keypress
            ''' Measure cost and write to file '''
            state = {'coils':{'I1':62.9, 'I2':65.5}}
            cost = self.pulsed_field(state)
            with open(self.data_path+'manual_alignment.txt', 'a') as file:
                string = ''
                for ax in range(dim):
                    string += '%f\t'%X[ax]
                string += '%f\n'%cost
                file.write(string)
