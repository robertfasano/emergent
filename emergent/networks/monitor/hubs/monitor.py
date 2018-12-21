from emergent.modules import Hub
from utility import experiment, trigger

class Monitor(Hub):
    def __init__(self, name, addr = None, network = None):
        super().__init__(name, addr, network)
        self.trigger_channel = 4
        self.ignored = ['labjack']          # add the names of any unpicklable attributes here

    @trigger
    def trigger(self):
        ''' Wait until TTL low, then return as soon as TTL high is detected '''
        while self.labjack.DIn(self.trigger_channel):
            continue
        while not self.labjack.DIn(self.trigger_channel):
            continue
        return True

    @experiment
    def monitor(self, state, params = {}):
        ''' A dummy experiment for standalone monitoring. '''
        print('sync')

        return self.labjack.DIn(self.trigger_channel)

    @experiment
    def measure_CH0(self, state, params = {}):
        return -self.labjack.AIn(0)

    @experiment
    def measure_CH1(self, state, params = {}):
        return -self.labjack.AIn(1)
