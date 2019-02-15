from emergent.modules import Hub, Watchdog
from emergent.utilities.decorators import experiment, trigger
import time

class Monitor(Hub):
    def __init__(self, name, addr = None, network = None, params = []):
        ''' Each entry in params should contain a name and params dict. '''
        super().__init__(name, addr = addr, network = network, params = params)
        self.trigger_channel = 'A4'

        from emergent.things.labjack import LabJack, MultiJack

        params_list = []
        for d in params['daqs']:
            params_list.append({})
            params_list[-1]['params'] = d['params']
            params_list[-1]['parent'] = self
            params_list[-1]['name'] = d['name']
        self.daq = MultiJack(params_list)
        for channel in params['watchdogs']:
            threshold = params['watchdogs'][channel]['threshold']
            units = params['watchdogs'][channel]['units']
            ch = params['watchdogs'][channel]['channel']
            self.watchdogs[channel] = Watchdog(parent = self, experiment = self.measure, name = channel, threshold = threshold, channel = ch, units = units)


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
    def monitor(self, state, params = {'delay': 1}):
        ''' A dummy experiment for standalone monitoring. '''
        time.sleep(params['delay'])
        return self.daq.DIn(self.trigger_channel)

    @experiment
    def measure(self, state, params = {'channel': 0}):
        return -self.daq.AIn(params['channel'])
