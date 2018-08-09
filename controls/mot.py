from archetypes.node import Control

class MOT(Control):
    def __init__(self, name, labjack, parent = None, path='.'):
        super().__init__(name, parent = parent, path=path)
        self.labjack = labjack

        ''' Power PMT '''
        self.labjack.AOut(3,-5, HV=True)
        self.labjack.AOut(2,5, HV=True)

    def stream(self, period = 1, amplitude = 0.1):
        key='coils.I1'
        self.cycle_time = period
        self.inputs[key].sequence = [(0,0), (period/2, amplitude)]
        data = self.clock.prepare_stream(key)

        self.labjack.stream_out(0, data)
