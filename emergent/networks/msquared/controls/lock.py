import numpy as np
from emergent.archetypes import Control
from utility import experiment, error
import datetime
import time
import numpy as np
from emergent.archetypes.parallel import ProcessHandler
class Lock(Control):
        def __init__(self, name, parent=None, path = '.'):
                super().__init__(name, parent, path=path)

        @experiment
        def detuning(self, state, params={'setpoint': 394798.3, 'wait': 0.1}):
            self.actuate(state)
            time.sleep(params['wait'])
            return np.abs(params['setpoint']-self.children['Wavemeter'].frequency())

        @error
        def error(self, state, params={'proportional_gain': 0.5, 'integral_gain': 0.05, 'setpoint': 394798.3, 'wait': 0.1}):
            self.actuate(state)
            time.sleep(params['wait'])
            return params['setpoint']-self.children['Wavemeter'].frequency()

        def PID(self, Kp=.5, Ki=0.05, Kd=0.0, sign = 1):
            if self.children['SolsTiS'].check_etalon_lock():
                self.children['SolsTiS'].lock(0)
            error_params={'setpoint': 394798.25, 'wait': 0.1}
            state = {'SolsTiS': self.state['SolsTiS']}
            self.optimizer, self.index = self.attach_optimizer(state, self.detuning)
            self.optimizer.PID(state, self.error, params={'proportional_gain':Kp, 'integral_gain':Ki, 'derivative_gain':Kd, 'sign':sign}, error_params = error_params)
