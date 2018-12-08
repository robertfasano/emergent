import numpy as np
from emergent.archetypes.node import Control
from utility import experiment, error
import datetime
import time
import numpy as np

class TestControl(Control):
        def __init__(self, name, parent=None, path = '.'):
                super().__init__(name, parent, path=path)
                self.sampler, index = self.attach_sampler(self.state, self.cost_uncoupled)

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
        def rosenbrock_banana(self, state, params={'a': 1, 'b': 100}):
            self.actuate(state)
            x = self.state['deviceA']['X']
            y = self.state['deviceA']['Y']
            return (params['a']-x)**2+params['b']*(y-x**2)**2

        @experiment
        def line_distance(self, state, params = {'amplitude': 1, 'y0': 0.5, 'yspan':0.5}):
            ''' Measures the distance from the point (X,Y) of deviceA and the line x-y = 0, modulated by a Gaussian envelope '''
            self.actuate(state)
            x = self.state['deviceA']['X']
            y = self.state['deviceA']['Y']
            d = np.abs(x-y)/np.sqrt(2)

            return d+params['amplitude']/np.exp(-(y-params['y0'])**2/params['yspan']**2)

        @experiment
        def cost_ramp(self, sequence, params = {'steps':10}):
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
        def error(self, state, params = {"cycle delay": 1, "drift rate": 1, "sign":-1, "proportional_gain": 0.5, "integral_gain": 0.25}):
            self.actuate(state)
            dev = list(state.keys())[0]
            input = list(state[dev].keys())[0]
            if not hasattr(self, 'start_time'):
                self.start_time = time.time()
            setpoint = params['drift rate']*(time.time()-self.start_time)
            e = self.state[dev][input] - setpoint
            e = -e
            print('Setpoint:',setpoint)
            time.sleep(params['cycle delay'])
            return(e)



        def scramble(self):
            for key in self.state.keys():
                self.state[key] = np.random.uniform()
