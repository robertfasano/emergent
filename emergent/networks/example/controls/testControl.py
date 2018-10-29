import numpy as np
from emergent.archetypes.node import Control
from utility import experiment
import datetime
import time
import numpy as np

class TestControl(Control):
        def __init__(self, name, parent=None, path = '.'):
                super().__init__(name, parent, path=path)

        def cost_coupled(self, state, params={}):
            return self.cost_uncoupled(state, theta=30*np.pi/180)

        @experiment
        def cost_uncoupled(self, state, params = {'theta':0, 'noise':0}):
            theta = params['theta']
            self.actuate(state)
            x=self.state['deviceA']['X']*np.cos(theta) - self.state['deviceA']['Y']*np.sin(theta)
            y=self.state['deviceA']['X']*np.sin(theta) + self.state['deviceA']['Y']*np.cos(theta)
            x0 = 0.3
            y0 = 0.6
            cost =  -np.exp(-(x-0.5)**2/x0**2)*np.exp(-(y-0.5)**2/y0**2) + np.random.normal(0, params['noise'])

            return cost

        @experiment
        def cost_ramp(self, sequence):
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

        def error(self, state):
            self.actuate(state)
            dev = list(state.keys())[0]
            input = list(state[dev].keys())[0]
            e = self.state[dev][input] - (time.time()-self.start_time)
            e = -e
            print('Setpoint:',time.time()-self.start_time)
            time.sleep(1)
            return(e)

        def demo_PID(self, Kp=.01, Ki=0, Kd=0, sign = -1):
            self.start_time = time.time()
            state = {'deviceA':{'X':0}}
            self.optimizer.PID(state, self.error, params={'proportional_gain':Kp, 'integral_gain':Ki, 'derivative_gain':Kd, 'sign':sign}, error_params = {})

        def optimize_sequence(self):
            self.clock.prepare_constant(1, 'deviceA.X', 15)
            s = self.get_subsequence(['deviceA.X'])
            self.optimizer.scipy_minimize(s, self.cost_ramp, params={'method':'Nelder-Mead', 'tol':4e-3, 'plot':0})
            self.optimizer.animate_sequence_history()


        def scramble(self):
            for key in self.state.keys():
                self.state[key] = np.random.uniform()
