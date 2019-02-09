import numpy as np
from emergent.modules import Hub, Watchdog, Sampler
from emergent.utilities.decorators import experiment, error, trigger

import datetime
import time
import numpy as np
import socket
import importlib

class DemoHub(Hub):
        def __init__(self, name, params = {}, addr=None, network=None):
                super().__init__(name, addr=addr, network = network, params = params)

        def cost_coupled(self, state, params={}):
            return self.cost_uncoupled(state, theta=30*np.pi/180)

        @trigger
        def trigger(self):
            print('triggered')
            return True

        @experiment
        def transmitted_power(self, state, params = {'sigma_x': 0.3, 'sigma_y': 0.8, 'x0': 0.3, 'y0': 0.6, 'noise':0, 'delay': 0.5}):
            self.actuate(state)
            x=self.state['MEMS']['X']
            y=self.state['MEMS']['Y']
            x0 = params['x0']
            y0 = params['y0']
            sigma_x = params['sigma_x']
            sigma_y = params['sigma_y']
            power =  np.exp(-(x-x0)**2/sigma_x**2)*np.exp(-(y-y0)**2/sigma_y**2) + np.random.normal(0, params['noise'])

            return -power



        @experiment
        def rosenbrock_banana(self, state, params={'a': 1, 'b': 100}):
            self.actuate(state)
            x = self.state['MEMS']['X']
            y = self.state['MEMS']['Y']
            return (params['a']-x)**2+params['b']*(y-x**2)**2

        @experiment
        def line_distance(self, state, params = {'amplitude': 1, 'y0': 0.5, 'yspan':0.5}):
            ''' Measures the distance from the point (X,Y) of MEMS and the line x-y = 0, modulated by a Gaussian envelope '''
            self.actuate(state)
            x = self.state['MEMS']['X']
            y = self.state['MEMS']['Y']
            d = np.abs(x-y)/np.sqrt(2)

            return d+params['amplitude']/np.exp(-(y-params['y0'])**2/params['yspan']**2)

        @experiment
        def cost_ramp(self, sequence, params = {'steps':10}):
            ''' Evaluate a cost function similar to an optical scattering force,
                which is maximized for a ramp x(t)=1/t. '''
            self.sequences = sequence
            s = sequence['MEMS.X']
            result = 0
            for i in range(len(s)):
                x = s[i][1]
                t = s[i][0]
                result -= 1/(1+(1-x*t)**2)
            return result

        @error
        def error(self, state, params = {"cycle delay": 1, "drift rate": 1}):
            self.actuate(state)
            thing = list(state.keys())[0]
            input = list(state[thing].keys())[0]
            if not hasattr(self, 'start_time'):
                self.start_time = time.time()
            setpoint = params['drift rate']*(time.time()-self.start_time)
            e = self.state[thing][input] - setpoint
            e = -e
            time.sleep(params['cycle delay'])

            print('Setpoint:',setpoint)
            return(e)



        def scramble(self):
            for key in self.state.keys():
                self.state[key] = np.random.uniform()
