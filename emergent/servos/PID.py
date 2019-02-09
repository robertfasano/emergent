from emergent.utilities.containers import Parameter
from emergent.utilities.decorators import servo
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
    def run(self, state, callback = None):
        error = self.sampler.experiment
        if callback is None:
            callback = self.sampler.callback
        things = list(state.keys())
        assert len(things) == 1
        thing = things[0]

        inputs = list(state[thing].keys())
        assert len(inputs) == 1
        input = inputs[0]
        input_node = self.sampler.hub.children[thing].children[input]
        input_node.error_history = pd.Series()
        last_error = error(state, self.sampler.experiment_params)
        last_time = time.time()
        integral = 0
        e = None
        while callback(e):
            e = error(state, self.sampler.experiment_params)
            t = time.time()
            self.sampler.history.loc[t,'cost']=e
            for thing in state:
                for input in state[thing]:
                    self.sampler.history.loc[t,thing+'.'+input] = state[thing][input]
            # print('State:', state, 'Error:', e)
            delta_t = t - last_time
            delta_e = e - last_error

            proportional = self.sampler.algorithm_params['Proportional gain'] * e
            integral += self.sampler.algorithm_params['Integral gain'] * e * delta_t
            derivative = self.sampler.algorithm_params['Derivative gain'] * delta_e/delta_t

            last_time = t
            last_error = e

            target = proportional + integral + derivative
            # print('Correction:', target)
            state[thing][input] -= self.sampler.algorithm_params['Sign']*target  # gets passed into error in the next loop

    def set_params(self, params):
        for p in params:
            self.params[p].value = params[p]
