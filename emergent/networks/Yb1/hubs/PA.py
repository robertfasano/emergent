from emergent.modules import Hub
from utility import experiment, extract_pulses, trigger, error
import numpy as np
import time

class Photoassociation(Hub):
    def __init__(self, name, addr = None, network = None):
        super().__init__(name = name, addr = addr, network = network)
        self.trigger_channel = 4
        self.ignored = ['labjack']          # add the names of any unpicklable attributes here
        self.servo_setpoint = -0.3

    @error
    def loop_filter_output(self, state, params={'wait': 0.1}):
        self.actuate(state)
        time.sleep(params['wait'])
        signal = []
        for i in range(int(params['cycles per sample'])):
            signal.append(self.labjack.AIn(0))
        return (np.mean(signal)-self.servo_setpoint)

    @trigger
    def trigger(self):
        ''' Wait until TTL low, then return as soon as TTL high is detected '''
        while self.labjack.DIn(self.trigger_channel):
            continue
        while not self.labjack.DIn(self.trigger_channel):
            continue
        return True

    @experiment
    def experiment(self, state, params = {'ramp time': 0.1, 'ramp points': 10}):
        f = state['synthesizer']['frequency']
        a = self.amplitude(f)

        # f0 = self.state['synthesizer']['frequency']
        # a0 = self.state['synthesizer']['amplitude']
        #
        # ''' Ramp the frequency and intensity to new target state '''
        # for i in range(int(params['ramp points'])):
        #     f_target = f0 + (i+1)/params['ramp points']*(f-f0)
        #     a_target = a0 + (i+1)/params['ramp points']*(a-a0)
        #     self.actuate({'synthesizer': {'frequency': f_target, 'amplitude': a_target}})
        #     time.sleep(params['ramp time']/params['ramp points'])

        self.actuate({'synthesizer': {'frequency': f, 'amplitude': a}})

        return 0

    def amplitude(self, f):
        ''' In units of dBm '''
        if f < 60:
            return -13
        elif f < 120:
            return -12
        elif f < 200:
            return -11
        elif f < 360:
            return -10
        elif f < 400:
            return -9
        elif f < 480:
            return -8
        elif f < 640:
            return -7
        else:
            return -6
