import sys
import numpy as np
sys.path.append('O:/Public/Yb clock')
from emergent.devices.genesys import Genesys
from emergent.archetypes.node import Device
from scipy.stats import linregress
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
    def __init__(self, port1, port2, parent = None, labjack = None):
        super().__init__(name='coils', parent = parent)
        self.port1 = port1
        self.port2 = port2
        self.labjack = labjack

        self.probe_coefficient = 2000/49.9
        params = self.params
        self.intercept = [params['intercept_1']['value'], params['intercept_2']['value']]
        self.slope = [params['slope_1']['value'], params['slope_2']['value']]

        self._connected = self._connect()

    def calibrate(self, coil, Vmin=1, Vmax=3, steps=100, delay = 1/100):
        ''' Measures and fits an IV curve '''
        V = np.linspace(Vmin, Vmax, steps)
        I = []
        for v in V:
            self.labjack.AOut(coil-1, v)
            I.append(self.measure_current(coil))
            time.sleep(delay)
        fit = linregress(V, I)
        self.slope[coil-1] = fit[0]
        self.intercept[coil-1] = fit[1]
        plt.figure()
        plt.plot(V, I)
        plt.xlabel('Setpoint (V)')
        plt.ylabel('Current (I)')
        plt.show()
        print('done')
        #self._save()
        #self._actuate(self.state)           # return to initial state
        self.labjack.AOut(coil-1, 0)

    def measure_current(self, coil):
        ''' Measures the Hall probe current '''
        i = coil-1
        current = self.labjack.AIn(i) * self.probe_coefficient #make sure monitor probes plugged in
        return current

    def _connect(self):
         try:
             self.coil1 = Genesys(port = self.port1, lowlevel = False)
             self.coil2 = Genesys(port = self.port2, lowlevel = False)
             print()
             self.coil1.set_current(80) #there's a bit of a naming ambiguity
             #b/c there are 2 current setting methods, 1 for the PSUs& 1 for the FETs
             self.coil2.set_current(80)
             self.calibrate(1)
             self.calibrate(2)
             return 1
         except Exception as e:
             print('Failed to connect to coils:', e)
             return 0

  #      return 1

    def _actuate(self, state):
        self.set_field(state['grad'], state['z0'])

    def set_current(self, coil, current):
        ''' Sets the current of the targeted coil. 0-5V corresponds to 0-100 A. '''
        i = coil-1
        voltage = (current-self.intercept[i])/self.slope[i]
        self.labjack.AOut(i, voltage)

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
        """Square pulse the B-field between 0 and a set configuration"""
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
