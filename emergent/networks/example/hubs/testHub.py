import numpy as np
from emergent.modules import Hub, Watchdog, Sampler
from emergent.utility import experiment, error
import datetime
import time
import numpy as np
import socket
import importlib

class TestWatchdog(Watchdog):
    def __init__(self, parent, name = 'watchdog'):
        super().__init__(parent, name)
        self.threshold = 0.5

    def validate_settings(self, settings):
        required_fields = ['state', 'experiment_name', 'hub', 'algorithm_params', 'experiment_params', 'algorithm']
        for field in required_fields:
            assert field in settings
        settings['callback'] = None
        if 'cycles per sample' not in settings['experiment_params']:
            settings['experiment_params']['cycles per sample'] = 1

        return settings

    def measure(self):
        ''' Measures power at the current state. This is an example of a signal that a Watchdog can monitor - if the Watchdog
            called the original @experiment, we would have recursion issues! '''
        x=self.parent.state['MEMS']['X']
        y=self.parent.state['MEMS']['Y']
        params = {'sigma_x': 0.3, 'sigma_y': 0.8, 'x0': 0.3, 'y0': 0.6, 'noise':0}
        x0 = params['x0']
        y0 = params['y0']
        sigma_x = params['sigma_x']
        sigma_y = params['sigma_y']
        power =  np.exp(-(x-x0)**2/sigma_x**2)*np.exp(-(y-y0)**2/sigma_y**2) + np.random.normal(0, params['noise'])

        return power

    def react(self):
        ''' Required fields for settings dict: state, experiment_name, algorithm_params, experiment_params, callback, cycles_per_sample '''
        experiment = getattr(self.parent, 'transmitted_power')
        experiment_params = {'sigma_x': 0.3, 'sigma_y': 0.8, 'x0': 0.3, 'y0': 0.6, 'noise':0, 'cycles per sample': 1}
        module = importlib.__import__('optimizers')
        algorithm = getattr(module, 'GridSearch')()
        sampler = Sampler(algorithm.name,
                          self.parent.state,
                          self.parent,
                          experiment,
                          experiment_params,
                          algorithm,
                          {'steps': 20},
                          t=0)
        sampler.algorithm.run(sampler.state)
        sampler.active = False

class TestHub(Hub):
        def __init__(self, name, addr=None, network=None):
                super().__init__(name, addr, network = network)
                self.watchdogs['watchdog'] = TestWatchdog(self, 'fiber power')

        def cost_coupled(self, state, params={}):
            return self.cost_uncoupled(state, theta=30*np.pi/180)

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
