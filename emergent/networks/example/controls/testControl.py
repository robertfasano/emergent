import numpy as np
from emergent.archetypes.node import Control
from utility import experiment, error
import datetime
import time
import numpy as np

class TestControl(Control):
        def __init__(self, name, parent=None, path = '.'):
                super().__init__(name, parent, path=path)

        def cost_coupled(self, state, params={}):
            return self.cost_uncoupled(state, theta=30*np.pi/180)

        @experiment
        def cost_uncoupled(self, state, params = {'sigma_x': 0.3, 'sigma_y': 0.8, 'x0': 0.3, 'y0': 0.6, 'theta':0, 'noise':0}):
            theta = params['theta']
            self.actuate(state)
            x=self.state['deviceA']['X']*np.cos(theta) - self.state['deviceA']['Y']*np.sin(theta)
            y=self.state['deviceA']['X']*np.sin(theta) + self.state['deviceA']['Y']*np.cos(theta)
            x0 = params['x0']
            y0 = params['y0']
            sigma_x = params['sigma_x']
            sigma_y = params['sigma_y']
            cost =  -np.exp(-(x-x0)**2/sigma_x**2)*np.exp(-(y-y0)**2/sigma_y**2) + np.random.normal(0, params['noise'])

            return cost

        @experiment
        def cost_ramp(self, sequence, params = {}):
            ''' Evaluate a cost function similar to an optical scattering force,
                which is maximized for a ramp x(t)=1/t. '''
            self.sequences = sequence
            s = sequence['deviceA.X']
            result = 0
            for i in range(len(s)):
                x = s[i][1]
                t = s[i][0]
                result -= 1/(1+(1-x*t)**2)
            return result

        @error
        def error(self, state, error_params = {"cycle delay": 1, "drift rate": 1, "sign":-1, "proportional_gain": 0.5, "integral_gain": 0.25}):
            self.actuate(state)
            dev = list(state.keys())[0]
            input = list(state[dev].keys())[0]
            if not hasattr(self, 'start_time'):
                self.start_time = time.time()
            setpoint = error_params['drift rate']*(time.time()-self.start_time)
            e = self.state[dev][input] - setpoint
            e = -e
            print('Setpoint:',setpoint)
            time.sleep(error_params['cycle delay'])
            return(e)

        def optimize_sequence(self):
            self.clock.prepare_constant(1, 'deviceA.X', 15)
            s = self.get_subsequence(['deviceA.X'])
            self.optimizer.scipy_minimize(s, self.cost_ramp, params={'method':'Nelder-Mead', 'tol':4e-3, 'plot':0})
            self.optimizer.animate_sequence_history()


        def scramble(self):
            for key in self.state.keys():
                self.state[key] = np.random.uniform()
