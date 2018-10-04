from emergent.archetypes.node import Control
from emergent.utility import experiment
import bristol671

class LatticeLock(Control):
    def __init__(self, params, laser, pzt, name='Lattice lock', parent=None, path='.'):
        super().__init__(name=name, parent = parent, path=path)
        self.parameters = params
        self.pzt = pzt
        self.laser = laser

        ''' Release etalon and PZT locks '''
        self.etalon.lock('off')
        self.PZT.lock('off')

        ''' Connect to wavemeter '''
        self.wavemeter = bristol671.BristolWM('TCPIP::10.199.199.1::23::SOCKET')
        #self.switch = BristolOFS()     # untested
        self.port = 0
        #self.switch.select(self.port)

    def acquire_cavity_lock(self, span = 0.05, step = .001, sweeps = 5):
        ''' Tune to magic '''
        points, costs = self.optimizer.grid_search({'PZT':self.state['PZT']}, self.detuning_cost, params={'steps':20})

        ''' Execute triangle-wave search'''
        #
        ''' Engage lock '''
        self.pzt.lock('on')
        ''' Start slow lock '''
        #

    def acquire_etalon_lock(self):
        self.etalon.lock('off')
        self.PZT.lock('off')

        points, costs = self.optimizer.grid_search({'SolsTiS':self.state['SolsTiS']}, self.detuning_cost, params={'steps':20})
        self.etalon_lock('on')

        ''' Make sure that frequency doesn't jump away from lock point '''
        time.sleep(1)
        c = self.detuning_cost(self.state)
        if c > self.parameters['etalon']['lock threshold']:
            log.warn('Etalon lock outside threshold by %f GHz; reacquiring...'%c)
            self.acquire_etalon_lock()
        else:
            log.info('Etalon locked within %f GHz of target frequency.'%c)

    def calibrate_etalon(self):
        ''' Calibrate relationship between etalon setpoint and frequency. '''
        return

    def calibrate_pzt(self):
        ''' Calibrate relationship between PZT voltage and frequency. '''
        return

    def get_frequency(self, window = 1):
        v = []
        for i in range(window):
            v.append(self.wavemeter.frequency()*1000)
        return np.mean(v)

    def check_resonance(self):
        return self.measure_cavity_transmission(self.state) > self.parameters['lock']['target voltage']

    def servo_etalon(self):
        ''' Keeps the etalon within a set threshold of target '''
        return

    def servo_pzt(self):
        ''' Keeps the PZT within a set threshold of target '''
        return

    @experiment
    def detuning_cost(self, state):
        self.actuate(state)
        return np.abs(self.get_frequency()-self.parameters['lock']['frequency'])

if __name__ == '__main__':
    params = {'lock':{}, 'etalon':{}}
    params['lock']['frequency'] = 394798.226
    params['lock']['target voltage'] = 0.8
    params['etalon']['lock threshold'] = 1
