from emergent.archetypes.node import Control
import time
from utility import cost

class MOT(Control):
    def __init__(self, name, labjack, parent = None, path='.'):
        super().__init__(name, parent = parent, path=path)
        self.labjack = labjack
        self.labjack.prepare_streamburst(channel=0)

        ''' Power PMT '''
        # self.labjack.AOut(3,-5, HV=True)
        # self.labjack.AOut(2,5, HV=True)
        self.labjack.AOut(7,-5, HV=True)
        self.labjack.AOut(6,5, HV=True)
    def stream(self, period = 1, amplitude = 0.1):
        key='coils.I1'
        self.cycle_time = period
        self.inputs[key].sequence = [(0,0), (period/2, amplitude)]
        data = self.clock.prepare_stream(key)

        self.labjack.stream_out(0, data)

    @cost
    def pulsed_slowing(self, state):
        ''' Toggle between high and low magnetic field; measure mean fluorescence
            in both cases and return the difference. '''
        self.actuate(state)
        self.labjack.AOut(0,0)
        time.sleep(0.05)
        self.labjack.AOut(1, 0) # output DC level for subtraction with SRS
        low = self.labjack.streamburst(duration=0.05, operation = 'mean')
        self.labjack.AOut(1, low) # output DC level for subtraction with SRS
        self.labjack.AOut(0,3.3)
        time.sleep(0.05)
        high = self.labjack.streamburst(duration=0.05, operation = 'mean')
        return -high    # low is subtracted out by SRS

    @cost
    def pulsed_field(self, state):
        ''' Toggle between high and low magnetic field; measure mean fluorescence
            in both cases and return the difference. '''
        self.actuate({'coils.I1':0, 'coils.I2':0})
        time.sleep(0.05)
        self.labjack.AOut(1, 0) # output DC level for subtraction with SRS
        low = self.labjack.streamburst(duration=0.1, operation = 'mean')
        self.labjack.AOut(1, low) # output DC level for subtraction with SRS
        self.actuate(state)
        time.sleep(0.05)
        high = self.labjack.streamburst(duration=0.1, operation = 'mean')
        return -high    # low is subtracted out by SRS


    def wave(self, frequency=2):
        V = 3.3
        seq = [[0,0], [1/frequency/2,V]]
        stream, scanRate = self.labjack.sequence2stream(seq, 1/frequency, 1)
        self.labjack.stream_out([0], stream, scanRate, loop = True)
