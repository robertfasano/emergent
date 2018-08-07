import sys
import numpy as np
sys.path.append('O:/Public/Yb clock')
from devices.genesys import Genesys
from archetypes.node import Device
from scipy.stats import linregress
from scipy.optimize import minimize
import matplotlib.pyplot as plt
plt.ion()
import time

#Constants
MU0 = 4*np.pi*1e-7
R1 = 0.080587
Z1 = -0.036605
N1 = 51.166136
R2 = 0.083645
Z2 = 0.037488
N2 = 48.869121

class CurrentDriver(Device):
    ''' Current driver for quadrupole coils using two TDK Genesys programmable
        power supplies and a bespoke current servo board. '''
    def __init__(self, name, port1, port2, parent = None, labjack = None):
        ''' Initialize the Device for use. '''
        super().__init__(name=name, parent = parent)
        self.port1 = port1
        self.port2 = port2
        self.labjack = labjack
        self.slope = [0,0]
        self.intercept = [0,0]

        self.probe_coefficient = 2000/49.9

        self.add_input('I1')
        self.add_input('I2')

        self.add_input('grad', type='virtual')
        self.add_input('zero', type='virtual')
        self._connected = self._connect()

    def calibrate(self, coil, Vmin=1, Vmax=3, steps=100, delay = 1/100, plot = False):
        ''' Measure and fit the IV curve of the FETs. '''
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
        #self._save()
        #self._actuate(self.state)           # return to initial state
        self.labjack.AOut(coil-1, 0)

    def measure_current(self, coil):
        ''' Measure the Hall probe current. '''
        i = coil-1
        current = self.labjack.AIn(i) * self.probe_coefficient #make sure monitor probes plugged in
        return current

    def _connect(self):
        ''' Connect to and initialize the power supplies, then run IV calibration. '''
        try:
             self.psu1 = Genesys(name='psu1', port = self.port1)
             self.psu2 = Genesys(name='psu2', port = self.port2)
             for psu in [self.psu1, self.psu2]:
                 psu.set_current(80)
                 psu.set_voltage(6)

             self.calibrate(1)
             self.calibrate(2)
             return 1
        except Exception as e:
             print('Failed to connect to coils:', e)
             return 0

    # def _actuate(self, state):
    #     ''' Set the gradient and zero position of the magnetic field. '''
    #     try:
    #         grad = state['grad']
    #     except KeyError:
    #         grad = self.state['grad']
    #     try:
    #         zero = state['zero']
    #     except KeyError:
    #         zero = self.state['zero']
    #     self.set_field(grad, zero)

    def _actuate(self, state):
        self.set_current(1, state['I1'])
        self.set_current(2, state['I2'])


    def set_current(self, coil, current):
        ''' Sets the current of the targeted coil. 0-5V corresponds to 0-100 A. '''
        i = coil-1
        voltage = (current-self.intercept[i])/self.slope[i]
        self.labjack.AOut(i, voltage)

    def real_to_virtual(self, state):
        ''' Converts a real state with currents I1, I2 to a virtual state with a
            gradient and zero. '''
        state = self.get_missing_keys(state, ['I1', 'I2'])
        I1 = state['I1']
        I2 = state['I2']

        ''' Find root numerically for zero of B-field '''
        res = minimize(fun=self.B, x0=0)
        z0 = res.x
        grad = 3*MU0/2 * (I2*N2*R2**2*(z0-Z2)/(R2**2+(z0-Z2)**2)**(5/2)-I1*N1*R1**2*(z0-Z1)/(R1**2+(z0-Z1)**2)**(5/2))

        ''' Convert units to mm and G/cm '''
        z0 *= 1000
        grad *= 100
        return {'zero':z0, 'grad':grad}

    def B(self, z):
        return MU0/2 * (N1*I1*R1**2/(R1**2+(z-Z1)**2)**(3/2)-N2*I2*R2**2/(R2**2+(z-Z2)**2)**(3/2))

    def virtual_to_real(self, state):
        ''' Converts a virtual state with gradient and zero into a real state with
            currents I1, I2. '''
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
        ''' Args: gradient in G/cm, z0 in mm. The zero position is relative
            to the center of the coils, along the axis pointing from coil 1
            to coil 2. '''
        z0 /= 1000
        grad /= 100
        denom = (z0-Z1)*(R2**2+(z0-Z2)*(Z1-Z2))-R1**2*(z0-Z2)
        alpha = 2/3/MU0 * (R1**2+(z0-Z1)**2)*(R2**2+(z0-Z2)**2)/denom
        I1 = alpha * (R1**2+(z0-Z1)**2)**(3/2)/N1/R1**2 * grad
        I2 = alpha * (R2**2+(z0-Z2)**2)**(3/2)/N2/R2**2 * grad
        self.set_current(1, I1)
        self.set_current(2, I2)

    def wave(self, frequency=1, duty_cycle=.5, reps=50, grad=50, z0=5):
        """Square pulse the B-field between 0 and a set configuration."""
        i = 0
        loop = True
        while loop:
            i = i + 1
            if i == reps:
                self.set_field(0, z0)
                loop = False
                print('done pulsing b-fields')
            elif i % 2:
                self.set_field(grad, z0)
                time.sleep(1/frequency*duty_cycle)
            else:
                self.set_current(1, 0)
                self.set_current(2, 0)
                time.sleep(1/frequency*(1-duty_cycle))
