from archetypes.node import Control

class MOT(Control):
    def __init__(self, name, labjack, parent = None, path='.'):
        super().__init__(name, parent = parent, path=path)
        self.labjack = labjack
        self.labjack.prepare_streamburst(channel=0)

    def stream(self, period = 1, amplitude = 0.1):
        key='coils.I1'
        self.cycle_time = period
        self.inputs[key].sequence = [(0,0), (period/2, amplitude)]
        data = self.clock.prepare_stream(key)

        self.labjack.stream_out(0, data)

    def pulsed_cost(self, state):
        ''' Toggle between high and low magnetic field; measure mean fluorescence
            in both cases and return the difference. '''

        self.actuate({'coils.grad':0, 'coils.zero':0})
        time.sleep(0.1)
        low = self.labjack.streamburst(duration=0.1, operation = 'mean')
        self.actuate(state)
        time.sleep(0.1)
        high = self.labjack.streamburst(duration=0.1, operation = 'mean')

        return high-low
