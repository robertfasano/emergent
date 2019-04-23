import numpy as np
from emergent.core import Hub
from emergent.utilities.decorators import experiment, error
import datetime
import time
import numpy as np
from emergent.core import ProcessHandler

class Lock(Hub):
    def __init__(self, name, network=None):
        super().__init__(name, network=network)
        self.watchdogs['Wavemeter'] = Watchdog(parent=self, experiment=self.frequency, name='wavemeter', threshold=0)

    @experiment
    def frequency(self, state, params = {}):
        return -self.devices['Wavemeter'].frequency()

    @error
    def error(self, state, params={'setpoint': 394798.3, 'wait': 0.1}):
        self.actuate(state)
        time.sleep(params['wait'])
        return params['setpoint']-self.devices['Wavemeter'].frequency()

    def PID(self, Kp=.25, Ki=0.2, Kd=0.0, sign = 1):
        if self.devices['SolsTiS'].check_etalon_lock():
            self.devices['SolsTiS'].lock(0)
        error_params={'setpoint': 394798.25, 'wait': 0.1}
        state = {'SolsTiS': self.state['SolsTiS']}
        self.optimizer, self.index = self.attach_optimizer(state, self.detuning)
        self.optimizer.PID(state, self.error, params={'proportional_gain':Kp, 'integral_gain':Ki, 'derivative_gain':Kd, 'sign':sign}, error_params = error_params)
