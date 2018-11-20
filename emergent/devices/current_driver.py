import sys
import numpy as np
sys.path.append('O:/Public/Yb clock')
from emergent.devices.genesys import Genesys
from emergent.archetypes.node import Device
from emergent.archetypes.parallel import ProcessHandler
from scipy.stats import linregress
from scipy.optimize import newton
import matplotlib.pyplot as plt
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
        self.enable_setpoint(1)
        self.disable_setpoint(2)
        self.slope = [26.2895, 26.0752]
        self.intercept = [-1.9746,-4.5531]

        self.probe_coefficient = 2000/49.9

        self.add_input('I1')
        self.add_input('I2')

        # self._connected = self._connect()

        ''' Wave options '''
        # self.options['Start wave']=self.wave
        # self.options['Stop wave'] = self.labjack.stream_stop
        self.options['Calibrate'] = self.calibrate


    def calibrate(self, coil=None, Vmin=1.5, Vmax=3, steps=10, delay = 5/100, plot = False):
        ''' Measure and fit the IV curve of the FETs.

            Args:
                coil (int): The coil to calibrate (1 or 2)
                Vmin (float): Lower bound of the voltage sweep.
                Vmax (float): Upper bound of the voltage sweep.
                steps (int): Number of steps in the voltage sweep.
                delay (float): Optional settling time between changing voltage and measuring.
                plot (bool): If True, plot the calibration curve.
        '''
        if coil is None:
            coils = [1,2]
        else:
            coils = [coil]
        for coil in coils:
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
        self.actuate(self.state)

    def enable_setpoint(self, ch):
        ''' Only works with ch = 1 or 2 '''
        self.labjack.DOut(6+ch-1,0)

    def disable_setpoint(self, ch):
        ''' Only works with ch = 1 or 2 '''
        self.labjack.DOut(6+ch-1,1)

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
        # self.calibrate(coil)

    def _connect(self):
        try:
            # for coil in [1,2]:
                # self._run_thread(target=self._connect_to_psu, args=(coil,), stoppable = False)
                # self._connect_to_psu(coil)
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

    def B(self, z, I1, I2):
        ''' Analytic model for the on-axis field as a function of known calibration constants.

            Args:
                z (float): On-axis position in m.
                I1 (float): Current of coil 1 in A.
                I2 (float): Current of coil 2 in A.
        '''

        return MU0/2 * (N1*I1*R1**2/(R1**2+(z-Z1)**2)**(3/2)-N2*I2*R2**2/(R2**2+(z-Z2)**2)**(3/2))

    def pulse(self, N=20, A=10, T=1):
        i=0
        for j in range(N):
            i = (i+1)%2
            self.set_current(2,i*A)
            time.sleep(T/2)

    def wave(self, frequency = 2, I1=65, I2=65):
        state = {'I1':I1, 'I2':I2}
        sequence = {}
        stream = {}
        for i in [1,2]:
            V = (state['I%i'%i]-self.intercept[i-1])/self.slope[i-1]
            seq = [[0,0], [1/frequency/2,V]]
            stream['I%i'%i], scanRate = self.labjack.sequence2stream(seq, 1/frequency, 2)
        data = np.array([stream['I1'],stream['I2']]).T
        self.labjack.stream_out([0,1], data, scanRate, loop = True)

    def wave_ttl(self, frequency = 2):
        ''' Starts a wave between the current setpoint and 0 '''
        sequence = {}
        seq = [[0,0], [1/frequency/2,1]]
        # stream, scanRate = self.labjack.sequence2stream(seq, 1/frequency, 2)
        # self.labjack.stream_out([0,1], data, scanRate, loop = True)
        self.labjack.PWM(6,frequency,50)
