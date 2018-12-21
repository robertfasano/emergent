from emergent.modules import Watchdog

class TestWatchdog(Watchdog):
    def __init__(self, parent, name = 'watchdog'):
        super().__init__(parent, name)
        self.threshold = 0.5

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
        self.reoptimize(self.parent.state, 'transmitted_power')
