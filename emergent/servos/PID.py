from utility import Parameter, servo
import numpy as np
import pandas as pd
import time

class PID():
    def __init__(self):
        ''' Define default parameters '''
        self.name = 'PID'
        self.params = {}
        self.params['Proportional gain'] = Parameter(name= 'Proportional gain',
                                            value = 1,
                                            min = 0,
                                            max = 100,
                                            description = 'Proportional gain')
        self.params['Integral gain'] = Parameter(name= 'Integral gain',
                                            value = 0.1,
                                            min = 0,
                                            max = 10,
                                            description = 'Integral gain')
        self.params['Derivative gain'] = Parameter(name= 'Derivative gain',
                                            value = 0,
                                            min = 0,
                                            max = 100,
                                            description = 'Derivative gain')
        self.params['Sign'] = Parameter(name= 'Sign',
                                            value = -1,
                                            min = -1,
                                            max = 1,
                                            description = 'Sign of correction')

    @servo
    def run(self, state, error, params={'Proportional gain':1, 'Integral gain':0, 'Derivative gain':0, 'Sign':-1}, error_params = {}, callback = None):
        self.sampler.initialize(state, error, params, error_params)
        if callback is None:
            callback = self.sampler.callback
        devices = list(state.keys())
        assert len(devices) == 1
        dev = devices[0]

        inputs = list(state[dev].keys())
        assert len(inputs) == 1
        input = inputs[0]
        input_node = self.sampler.parent.children[dev].children[input]
        input_node.error_history = pd.Series()
        last_error = error(state, error_params)
        last_time = time.time()
        integral = 0
        e = None
        while callback(e):
            e = error(state, error_params)
            t = time.time()
            print(t)
            self.sampler.history.loc[t,'cost']=e
            for dev in state:
                for input in state[dev]:
                    self.sampler.history.loc[t,dev+'.'+input] = state[dev][input]
            print('State:', state, 'Error:', e)
            delta_t = t - last_time
            delta_e = e - last_error

            proportional = params['Proportional gain'] * e
            integral += params['Integral gain'] * e * delta_t
            derivative = params['Derivative gain'] * delta_e/delta_t

            last_time = t
            last_error = e

            target = proportional + integral + derivative
            state[dev][input] -= params['Sign']*target  # gets passed into error in the next loop

    def set_params(self, params):
        for p in params:
            self.params[p].value = params[p]
