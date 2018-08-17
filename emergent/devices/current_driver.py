import sys
import numpy as np
sys.path.append('O:/Public/Yb clock')
from emergent.devices.genesys import Genesys
from emergent.archetypes.node import Device
from emergent.archetypes.parallel import ProcessHandler
from scipy.stats import linregress
from scipy.optimize import newton
import matplotlib.pyplot as plt
plt.ion()
import time
import logging as log

#Constants
MU0 = 4*np.pi*1e-7
R1 = 0.080587
Z1 = -0.036605
N1 = 51.166136
R2 = 0.083645
Z2 = 0.037488
N2 = 48.869121

class CurrentDriver(Device, ProcessHandler):
    ''' Current driver for quadrupole coils using two TDK Genesys programmable
        power supplies and a bespoke current servo board. '''

    def __init__(self, name, port1, port2, parent = None, labjack = None):
        ''' Initialize the Device for use.

            Args:
                name (str): Name of Device node.
                port1 (str): Serial port for the first power supply (e.g. 'COM1').
                port2 (str): Serial port for the second power supply (e.g. 'COM2').
                parent (str): Name of the parent Control node.
                labjack (archetypes.labjackT7.LabJack): LabJack instance to use.
        '''
        Device.__init__(self, name=name, parent = parent)
        ProcessHandler.__init__(self)
        self.port1 = port1
        self.port2 = port2
        self.labjack = labjack
        self.slope = [0,0]
        self.intercept = [0,0]

        self.probe_coefficient = 2000/49.9

        self.add_input('I1')
        self.add_input('I2')

        self.add_input('grad', type='secondary')
        self.add_input('zero', type='secondary')
        # self._connected = self._connect()

        ''' Wave options '''
        self.options['Start wave']=self.wave
        self.options['Stop wave'] = self.labjack.stream_stop


    def calibrate(self, coil, Vmin=1.5, Vmax=3, steps=10, delay = 5/100, plot = False):
        ''' Measure and fit the IV curve of the FETs.

            Args:
                coil (int): The coil to calibrate (1 or 2)
                Vmin (float): Lower bound of the voltage sweep.
                Vmax (float): Upper bound of the voltage sweep.
                steps (int): Number of steps in the voltage sweep.
                delay (float): Optional settling time between changing voltage and measuring.
                plot (bool): If True, plot the calibration curve.
        '''
        V = np.linspace(Vmin, Vmax, steps)
        I = []
        for v in V:
            self.labjack.AOut(coil-1, v)
            I.append(self.measure_current(coil))
            time.sleep(delay)
        fit = linregress(V, I)
        self.slope[coil-1] = fit[0]
        self.intercept[coil-1] = fit[1]

        if plot:
            plt.figure()
            plt.plot(V, I)
            plt.xlabel('Setpoint (V)')
            plt.ylabel('Current (I)')
            plt.show()
        self.labjack.AOut(coil-1, 0)

    def measure_current(self, coil):
        ''' Measure the Hall probe current.

            Args:
                coil (int): 1 or 2
        '''
        i = coil-1
        current = self.labjack.AIn(i) * self.probe_coefficient #make sure monitor probes plugged in
        return current

    def _connect_to_psu(self, coil):
        ''' Connects to the Genesys power supply for coil 1 or 2. '''
        psu = Genesys(name='psu%i'%coil, port = getattr(self, 'port%i'%coil))
        psu._connect()
        setattr(self, 'psu%i'%coil, psu)
        psu.set_current(80)
        psu.set_voltage(6)
        self.calibrate(coil)

    def _connect(self):
        try:
            for coil in [1,2]:
                # self._run_thread(target=self._connect_to_psu, args=(coil,), stoppable = False)
                self._connect_to_psu(coil)
            return 1
        except Exception as e:
             log.error('Failed to connect to coils:', e)
             return 0

    def _actuate(self, state):
        ''' Set the current of each coil.

            Args:
                state (dict): State dict containing target currents in amps, e.g. {'I1':50, 'I2':40}.
        '''
        for key in state.keys():
            coil = int(key[1])
            self.set_current(coil, state[key])

    def set_current(self, coil, current):
        ''' Sets the current of the targeted coil based on the IV calibration.
            Args:
                coil (int): 1 or 2
                current (float): target current
        '''
        i = coil-1
        voltage = (current-self.intercept[i])/self.slope[i]
        self.labjack.AOut(i, voltage)

    def primary_to_secondary(self, state):
        ''' Converts a primary state with currents I1, I2 to a secondary state with a
            gradient and zero.

            Args:
                state (dict): State dict with primary currents in amps, e.g. {'I1':50, 'I2':40}.
            Returns:
                secondary_state (dict): State dict with gradient in G/cm and zero position in mm, e.g. {'grad':50, 'zero':0}.
        '''
        state = self.get_missing_keys(state, ['I1', 'I2'])
        I1 = state['I1']
        I2 = state['I2']

        ''' Find root numerically for zero of B-field. WARNING: if a zero
            is not found (e.g. if the current disparity is too great), then we
            set the result to zero.'''
        try:
            res = newton(func=self.B, args=(I1,I2), x0=0)
        except RuntimeError:
            log.warn('CurrentDriver zero could not be calculated.')
            res = 0
        z0 = res
        grad = -3*MU0/2 * (I2*N2*R2**2*(z0-Z2)/(R2**2+(z0-Z2)**2)**(5/2)-I1*N1*R1**2*(z0-Z1)/(R1**2+(z0-Z1)**2)**(5/2))

        ''' Convert units to mm and G/cm '''
        z0 *= 1000
        grad *= 100
        return {'zero':z0, 'grad':grad}

    def B(self, z, I1, I2):
        ''' Analytic model for the on-axis field as a function of known calibration constants.

            Args:
                z (float): On-axis position in m.
                I1 (float): Current of coil 1 in A.
                I2 (float): Current of coil 2 in A.
        '''

        return MU0/2 * (N1*I1*R1**2/(R1**2+(z-Z1)**2)**(3/2)-N2*I2*R2**2/(R2**2+(z-Z2)**2)**(3/2))

    def secondary_to_primary(self, state):
        ''' Converts a secondary state with gradient and zero into a primary state with
            currents I1, I2.

            Args:
                state (dict): State dict with gradient in G/cm and zero position in mm, e.g. {'grad':50, 'zero':0}.
            Returns:
                primary_state (dict): State dict with primary currents in amps, e.g. {'I1':50, 'I2':40}.
        '''
        state = self.get_missing_keys(state, ['grad', 'zero'])
        z0 = state['zero']
        grad = state['grad']

        z0 /= 1000
        grad /= 100
        denom = (z0-Z1)*(R2**2+(z0-Z2)*(Z1-Z2))-R1**2*(z0-Z2)
        alpha = 2/3/MU0 * (R1**2+(z0-Z1)**2)*(R2**2+(z0-Z2)**2)/denom
        I1 = alpha * (R1**2+(z0-Z1)**2)**(3/2)/N1/R1**2 * grad
        I2 = alpha * (R2**2+(z0-Z2)**2)**(3/2)/N2/R2**2 * grad

        return {'I1':I1, 'I2':I2}

    def set_field(self, grad, z0):
        ''' Sets coil currents to achieve the desired gradient and zero position.

            Args:
                gradient (float): Magnetic field gradient at the zero position, in G/cm.
                z0 (float): offset of the zero position from the center of the coils in mm, along the axis pointing from coil 1 to coil 2.
            '''
        state = self.secondary_to_primary({'grad':grad, 'zero':z0})
        self.set_current(1, state['I1'])
        self.set_current(2, state['I2'])


    def pulse(self, N=20, A=10, T=1):
        i=0
        for j in range(N):
            i = (i+1)%2
            self.set_current(2,i*A)
            time.sleep(T/2)

    def wave(self):
        frequency = 1
        grad = 50
        zero = 0
        state = self.secondary_to_primary({'grad':grad, 'zero':zero})
        sequence = {}
        stream = {}
        for i in [1,2]:
            V = (state['I%i'%i]-self.intercept[i-1])/self.slope[i-1]
            seq = [[0,0], [1/frequency/2,V]]
            stream['I%i'%i], scanRate = self.labjack.sequence2stream(seq, 1/frequency, 2)
        data = np.array([stream['I1'],stream['I2']]).T
        self.labjack.stream_out([0,1], data, scanRate, loop = True)