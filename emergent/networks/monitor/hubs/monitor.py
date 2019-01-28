from emergent.modules import Hub, Watchdog
from utility import experiment, trigger

class Monitor(Hub):
    def __init__(self, name, addr = None, network = None, params = {}):
        super().__init__(name, addr = addr, network = network, params = params)
        self.trigger_channel = 4

        if self.params['daq']['type'] == 'labjack':
            from emergent.things.labjack import LabJack
            devid = self.params['daq']['addr']
            self.daq = LabJack(params = {'devid': devid}, name='labjack', parent = self)

        for channel in params['watchdogs']:
            threshold = params['watchdogs'][channel]['threshold']
            ch = params['watchdogs'][channel]['channel']
            self.watchdogs[channel] = Watchdog(parent = self, experiment = self.monitor, name = channel, threshold = threshold, channel = ch)


        self.ignored = ['daq']          # add the names of any unpicklable attributes here

    @trigger
    def trigger(self):
        ''' Wait until TTL low, then return as soon as TTL high is detected '''
        while self.daq.DIn(self.trigger_channel):
            continue
        while not self.daq.DIn(self.trigger_channel):
            continue
        return True

    @experiment
    def sync(self, state, params = {}):
        ''' A dummy experiment for standalone monitoring. '''
        print('sync')

        return self.labjack.DIn(self.trigger_channel)

    @experiment
    def monitor(self, state, params = {'channel': 0}):
        return -self.daq.AIn(params['channel'])
