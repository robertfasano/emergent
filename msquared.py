import json
import socket
import numpy as np
import time
import sys
import os
import astropy.time
from threading import Thread
from scipy import stats
from PyQt5.QtWidgets import QApplication
import datetime
try:
    sys.path.remove('C:\\ProgramData\\Anaconda3\\lib\\site-packages\\mcdaq-1-py3.6.egg')
except ValueError:
    pass
if os.name == 'posix':        # if using OS X, open a special testing version of the program
    sys.path.append('/Users/rjf2/Documents/GitHub')
else:
    sys.path.append('C:\\Users\\Public\\Documents\\GitHub')
#    sys.path.append('C:\\Users\\Robbie\\Documents\\GitHub')
    sys.path.insert(0, 'C:\\Users\\yblab\\Python\\mcdaq')
    sys.path.insert(0, 'O:\\Public\\Yb clock')
#    import mcdaq
from labAPI import daq, optimize, gui
import bristol671     # note: this MUST be after mcdaq import, since bristol imports a different version
import matplotlib.pyplot as plt
plt.ion()
        
class MSquared():
    def __init__(self, parameters, tab):
        self.parameters = parameters
        self.tab = tab
        
        ''' Open socket connection '''
        server = "192.168.1.207"
        port = 39933
        client = "192.168.1.1"
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.client.connect((server, port))
        self.message(op = 'start_link', parameters = {'ip_address': client}, destination='laser')

        ''' Connect to wavemeter '''
        self.wavemeter = bristol671.BristolWM('TCPIP::10.199.199.1::23::SOCKET')
#        self.switch = BristolOFS()     # untested
        self.port = 0
#        self.switch.select(self.port)
        
        ''' Connect to DAC and ADC '''
        self.daq = daq.MCDAQ({'device':'USB-3105', 'id':'111696'}, function = 'output')
        self.adc = daq.MCDAQ({'device':'USB-2408', 'id':'1C96FD5'}, function = 'input', arange = 'BIP10VOLTS')
        
        ''' Configure lock process settings '''
        self.threads = {}
        self.cavity_lock = 0
        self.etalon_fail_count = 0
        self.max_etalon_fails = 5
        self.abort = 0
        self.sweeps = 5
        self.calibrated = 1
        self.load_setpoint()
        self.polynomial_order = 3
        self.etalon_lock = self.check_etalon_lock()
        self.etalon = self.parameters['Etalon']['Setpoint']
        if not self.etalon_lock or np.abs(self.cost()) > self.parameters['Etalon']['Lock threshold']:
            self.disengage_etalon_lock()
            self.actuate_etalon(self.parameters['Etalon']['Setpoint'])
#        self.actuate_pzt(self.parameters['PZT']['Setpoint'])
        self.actuate_pzt(0)
        self.locked = 0
        
    def acquire_cavity_lock(self, span = 0.05, step = .001, sweeps = 5):
        ''' At this point, the etalon should be locked and the PZT should be tuned to magic. We now start sweeping the PZT
            in another thread while monitoring the transmission in this thread. Note that the one-way latency between computers
            is about 300 ms, so the sweep must be sufficiently slow to allow locking at the right frequency.'''

#        threshold = 5
        center = self.pzt
        while True:
#            X = self.oscillator(self.pzt, span, step)
            ''' We want to search around a center point with increasing amplitude. '''
            
            X = np.arange(center-span/2, center+span/2, step)
            Y = np.abs(X-np.mean(X))
            X = X[Y.argsort()]
            
            t = []
            v = []
            peak_found = False
            for x in X:
                self.cavity_transmission = self.get_cavity_transmission()
                t.append(self.cavity_transmission)
                v.append(x)

                if self.cavity_transmission > self.parameters['Lock']['Target voltage']:
#                    print('Cavity transmission exceeds threshold; lock is engaged.')
#                    plt.figure()
#                    plt.semilogy(v,t, '.')
#                    plt.xlabel('Voltage (V)')
#                    plt.ylabel('Transmission (V)')
#        
#                    time.sleep(.05)
#                    plt.show()
                    return
#                sigma = np.std(t)
#                if sigma != 0:
#                    z = (np.max(t) - np.mean(t))/sigma
#                    if z>threshold: 
#                        print('%f-sigma peak detected (sigma = %f).'%(z, sigma))
#                        peak_found = True
#                        factor = 2/np.abs(z)
#                        span *= factor
#                        print('Recentering with span decreased by a factor of ', z/2)
#                        self.actuate_pzt(v[np.argmax(t)])
#                        break

                self.actuate_pzt(x)
            if not peak_found:
#                self.actuate_pzt(v[np.argmax(t)])
                span *= 1.25
                step /= 1.25
            if np.abs(self.cost()) > .015:
#                print('Retuning cavity to prevent drift.')
                self.tune_cavity(quit_function = self.resonant)

#            plt.figure()
#            plt.semilogy(v,t, '.')
#            plt.xlabel('Voltage')
#            plt.ylabel('Transmission')
#
#            time.sleep(.05)
#            plt.show()
#            print('Sweep complete. Increasing range...')

    
    def acquire_etalon_lock_failsafe(self):
        ''' Occasionally the etalon will repeatedly jump away from the lock point.
            In this case, rather than naively tuning back to the target frequency and
            repeating, we should start a new optimization problem where we try to optimize
            the post-lock cost as a function of pre-lock frequency '''
        self.actuate_pzt(0)
        step = 0.01
        span = .1
        X = np.arange(self.etalon-span/2, self.etalon+span/2, step)
        c = []
        while True:
            for x in X:
                if self.abort:
                    return
                self.actuate_etalon(x)
                self.engage_etalon_lock()
                c.append(self.cost())
                time.sleep(1)
                if np.abs(c[-1]) < self.parameters['Etalon']['Lock threshold']:
                    print('Etalon lock engaged at %f GHz.'%(c[-1]+self.parameters['Lock']['Frequency']))
                    return
                self.disengage_etalon_lock()
                print('Failed lock attempt: ', x, c[-1])
            
    def acquire_etalon_lock(self, zoom = 1, x = [], c = []):
        self.disengage_etalon_lock()
        self.disengage_gain()
        if self.abort:
            print('Aborting etalon lock.')
            return
        
#        if np.abs(self.cost()) > 10:
#            self.calibrate_etalon(self.etalon, 5, 25, delay = 0)
#        else:
#            self.calibrate_etalon(self.etalon, 1, 25, delay = 0)
        x0, c0 = self.tune_etalon(zoom = zoom)
        x.append(x0)
        c.append(c0)
#        try:
#            plt.figure()
#            plt.plot(x,c)
#            plt.xlabel('Etalon tune (%)')
#            plt.ylabel(r'$f-f_0$')
#            time.sleep(.05)
#            plt.show()
#        except ValueError:
#            pass
        self.engage_etalon_lock()
        time.sleep(1)
        f = self.get_frequency()
        if np.abs(f-self.parameters['Lock']['Frequency']) > self.parameters['Etalon']['Lock threshold'] and self.etalon_fail_count < self.max_etalon_fails:
            msg = 'Lock outside threshold at %f GHz, reacquiring...'%f
            print(msg)
#            self.acquire_etalon_lock(zoom = 1, x = x, c = c)
            self.disengage_etalon_lock()
            self.acquire_etalon_lock_failsafe()
            self.etalon_fail_count += 1
#        elif np.abs(f-self.parameters['Lock']['Frequency']]) > self.parameters['Etalon']['Lock threshold'] and self.etalon_fail_count >= self.max_etalon_fails:
#            msg = 'Maximum etalon failures occurred, aborting locking routine.'
#            self.etalon_fail_count = 0
#            self.abort = 1
        else:
            msg = 'Etalon locked at f=%f GHz.'%f
            self.parameters['Etalon']['Setpoint'] = self.etalon
#            self.save_setpoint()
            with open('etalon_settings.txt', 'w') as file:
                file.write(str(self.etalon))
            print(msg)
            self.etalon_fail_count = 0

    def actuate_pzt(self, value):
        self.pzt = value
        self.daq.out(6, value)
        time.sleep(self.parameters['PZT']['Tuning delay'])
        return 
        
    def actuate_etalon(self, value):
        self.etalon = value
        self.message(op = 'tune_etalon', parameters = {'setting': [self.etalon]}, destination = 'laser')
        time.sleep(self.parameters['Etalon']['Tuning delay'])
        return 
        

    def calibrate(self):
        self.abort = 1
        while self.locked:
            continue
        self.abort = 0
        self.actuate_pzt(0)
        self.calibrate_etalon(self.etalon, 2, steps = 15)
        
        while True:
            if self.abort:
                return
            self.acquire_etalon_lock()
            time.sleep(1)
            if np.abs(self.cost()) < self.parameters['Etalon']['Lock threshold']:
                break
            print('Etalon lock lost... reacquiring.')
        self.calibrate_pzt(V0 = self.pzt, span = 3, steps = 15)
        
    def calibrate_etalon(self, x0, span, steps = 30, sweeps = 1, delay = 0.01, filename = None):
        ''' Calibrates the relationship between etalon tuning and frequency. If a filename is specified, the calibration curve is saved. '''
        print('Calibrating etalon tuning frequency curve.')
        self.abort = 0
        self.disengage_gain()
        self.disengage_etalon_lock()
        self.actuate_pzt(0)
        X0 = np.linspace(x0-span/2, x0+span/2, int(steps))
        X = X0
        for i in range(int(sweeps)-1):
            if not i % 2:
                X = np.append(X, X0[::-1][1::])
            else:
                X = np.append(X, X0[1::])
        V = []
        f = []
        T = []
        for x in X:
            if self.abort:
                print('Calibration process aborted.')
                return
            self.actuate_etalon(x)
            time.sleep(delay)
            f.append(self.get_frequency())
            status = self.get_system_status()
            V.append(status['etalon_voltage'][0])
            T.append(status['temperature'][0])
#            print(v, f[-1])
        
        inds = np.argsort(X)
        
        def reorder(arr, inds):
            arr = np.array(arr)
            arr = arr[inds]
            arr = np.delete(arr, range(int(sweeps)))
            return arr
        
        X = reorder(X, inds)
        f = reorder(f, inds)
        V = reorder(V, inds)
        T = reorder(T, inds)
        
        plt.figure()
        plt.plot(X, np.array(f)-self.parameters['Lock']['Frequency'], '.')
        plt.xlabel('Etalon tuning (%)')
        plt.ylabel('Detuning (GHz)')
        self.parameters['Etalon']['Slope'], self.parameters['Etalon']['Intercept'], r_value, p_value, std_err = stats.linregress(X, f)
        char = {1:'+', -1:'-'}[np.sign(self.parameters['Etalon']['Slope'])]
        fit = np.polyfit(X, f, self.polynomial_order)
        string = r'f = '
        for i in range(len(fit)):
            string += r'%.1fx^%i'%(fit[i], i)
#        string = 'f = %f %s %f/%%'%(self.parameters['Etalon']['Intercept'], char, np.abs(self.parameters['Etalon']['Slope']))
        plt.title(string)
        time.sleep(0.05)
        plt.show()
        if filename != None:
            plt.savefig(filename.replace('txt', 'png'))
        self.calibrated_etalon = 1
#        self.save_setpoint()
        
        if filename != None:
            with open(filename, 'w') as file:
                file.write('x0=%f\tspan=%f\tsteps=%i\tsweeps=%i\tdelay=%f\tslope=%f\tintercept=%f\n'%(x0, span, steps, sweeps, delay, self.parameters['Etalon']['Slope'], self.parameters['Etalon']['Intercept']))
                file.write('Etalon tuning\tEtalon voltage\tFrequency\tTemperature\n')
                for i in range(len(f)):
                    file.write('%f\t%f\t%f\t%f\n'%(X[i], V[i], f[i], T[i]))
            print('Saved calibration data to %s.'%(filename))
                       
        ''' Identify magic frequency if in span '''
        f0 = self.parameters['Lock']['Frequency']
#        if f0 < np.max(f) and f0 > np.min(f):
        x0 = self.convert_frequency_to_etalon(f0)
        if x0 > 0 and x0 < 100:
            self.actuate_etalon(x0)
            self.engage_etalon_lock()
        
    def calibrate_pzt(self, V0 = None, span = 2, steps = 50, sweeps = 1, delay = 0, filename = None):
        ''' Calibrates the relationship between PZT voltage and frequency. If a filename is specified, the calibration curve is saved. '''
        self.abort = 0
        print('Calibrating PZT voltage frequency curve.')
        self.disengage_gain()
        X = np.linspace(V0-span/2, V0+span/2, int(steps))
        V = X
        for i in range(int(sweeps)-1):
            if not i % 2:
                V = np.append(V, X[::-1][1::])
            else:
                V = np.append(V, X[1::])
        f = []
        for v in V:
            if self.abort:
                print('Calibration process aborted.')
                return
            self.actuate_pzt(v)
            time.sleep(delay)
            f.append(self.get_frequency())
    #            print(v, f[-1])
        V = np.delete(V,0)
        del f[0]
        plt.figure()
        plt.plot(V, np.array(f)-self.parameters['Lock']['Frequency'])
        plt.xlabel('DAC voltage (V)')
        plt.ylabel('Detuning (GHz)')
        self.parameters['PZT']['Slope'], self.parameters['PZT']['Intercept'], r_value, p_value, std_err = stats.linregress(V, f)
        fit = np.polyfit(V, f, self.polynomial_order)
        string = r'f = '
        for i in range(len(fit)):
            string += r'%.1fV^%i'%(fit[i], i)
#        string = 'f = %f + %fV'%(self.parameters['PZT']['Intercept'], self.parameters['PZT']['Slope'])
        plt.title(string)
        time.sleep(0.05)
        plt.show()
        if filename != None:
            plt.savefig(filename.replace('txt', 'png'))
        self.calibrated_pzt = 1

#        self.save_setpoint()
        
        if filename != None:
            with open(filename, 'w') as file:
                file.write('V0=%f\tspan=%f\tsteps=%i\tsweeps=%i\tdelay=%f\tslope=%f\tintercept=%f\n'%(V0, span, steps, sweeps, delay, self.parameters['PZT']['Slope'], self.parameters['PZT']['Intercept']))
                file.write('PZT voltage\tFrequency\n')
                for i in range(len(f)):
                    file.write('%f\t%f\n'%(V[i], f[i]))
                    
        V0 = self.convert_frequency_to_voltage(self.parameters['Lock']['Frequency'])
        if V0 > -10 and V0 < 10:
            self.actuate_pzt(V0)
            print('PZT set to %f.'%V0)
        
    def center_cavity_lock(self, relative_gain = 1):
        self.pzt = optimize.line_search(x0 = self.pzt, cost = self.get_servo_output, actuate = self.actuate_pzt, step = self.parameters['Lock']['Slow gain'] * relative_gain, threshold = self.parameters['Lock']['Center threshold'], gradient = False, quit_function = self.unresonant) 

    def center_pzt(self):
        ''' Resets the PZT to 0 and re-engages the etalon lock. Should be done once in a while
            to avoid drifting out of DAC range. '''
        self.abort = 0
        self.actuate_pzt(0)
        self.acquire_etalon_lock()
        
    def check_etalon_lock(self):
        reply = self.message(op='etalon_lock_status', parameters = {}, destination = 'laser')
        return {'on':1, 'off':0}[reply['message']['parameters']['condition']]

    def convert_frequency_to_etalon(self, f):
        self.parameters['Etalon']['Intercept'] = self.get_frequency() - self.parameters['Etalon']['Slope'] * self.etalon
        return (f-self.parameters['Etalon']['Intercept'])/self.parameters['Etalon']['Slope']

    def convert_frequency_to_voltage(self, f):
        ''' Returns a calibrated voltage V corresponding to a target frequency f '''
#        if not self.calibrated:
#            self.calibrate_pzt()
        ''' Calculate new intercept based on observation '''
        self.parameters['PZT']['Intercept'] = self.get_frequency() - self.parameters['PZT']['Slope'] * self.pzt
        return (f-self.parameters['PZT']['Intercept'])/self.parameters['PZT']['Slope']
    
    def convert_etalon_to_frequency(self, X):
        ''' Returns a calibrated frequency f corresponding to an input etalon tuning X '''
        ''' Calculate new intercept based on observation '''
        self.parameters['Etalon']['Intercept'] = self.get_frequency() - self.parameters['Etalon']['Slope'] * self.etalon
        return self.parameters['Etalon']['Intercept'] + self.parameters['Etalon']['Slope'] * X
    
    def convert_voltage_to_frequency(self, V):
        ''' Returns a calibrated frequency f corresponding to an input voltage V '''
#        if not self.calibrated:
#            self.calibrate_pzt()
        ''' Calculate new intercept based on observation '''
        self.parameters['PZT']['Intercept'] = self.get_frequency() - self.parameters['PZT']['Slope'] * self.pzt
        return self.parameters['PZT']['Intercept'] + self.parameters['PZT']['Slope'] * V
    
    def cost(self):
        return self.get_frequency()-self.parameters['Lock']['Frequency']

    def disengage_etalon_lock(self):
        self.message(op = 'etalon_lock', parameters = {'operation': 'off'}, destination = 'laser')

    def disengage_gain(self):
        self.daq.out(13,10)             
        self.daq.out(0, 10)
    
    def engage_gain(self, target = 'both'):
        if target == 'fast':
            self.daq.out(0, 0)
        elif target == 'slow':
            self.daq.out(13,0)    
        else:
            self.daq.out(0, 0)
            self.daq.out(13,0) 
        
    def engage_etalon_lock(self):
        self.message(op = 'etalon_lock', parameters = {'operation': 'on'}, destination = 'laser')

    def get_cavity_transmission(self):
        return self.adc.read(0)

    def get_servo_output(self):
        return self.adc.read(1)
    
    def get_frequency(self, window = 1):
        v = []
        for i in range(window):
            v.append(self.wavemeter.frequency()*1000)
        return np.mean(v)
    
    def get_system_status(self):
        reply = self.message(op = 'get_status', parameters = {}, destination = 'laser')
        return reply['message']['parameters']
    
    def load_setpoint(self):
        with open('lattice_settings.txt', 'r') as file:
            self.parameters = json.load(file)
            
    def lock(self, hold = True, relock = False):
#        print('Beginning lock routine.')
#        self.load_parameters()
        time0 = time.time()
        self.abort = 0
#        self.parameters = parameters    # an artifact of the two-PC architecture
#        self.actuate_pzt(self.pzt) 

        ''' Etalon locking '''
        self.etalon_lock = self.check_etalon_lock()
        
        if np.abs(self.cost()) > self.parameters['Etalon']['Lock threshold'] or not self.etalon_lock:
            self.disengage_gain() 
#            print('Etalon unlocked; acquiring lock now... ')
            self.acquire_etalon_lock()
        if self.abort:
            print('Locking process aborted.')
            return
        
        ''' Tune near magic '''
        self.engage_gain('fast')
        if np.abs(self.cost()) > self.parameters['PZT']['Tuning threshold']:
            msg = 'Applying gain and tuning to target frequency.'
            print(msg)
            self.tune_cavity(quit_function = self.resonance_search)           # reset again in case adding gain shifted the frequency
        if self.abort:
            print('Locking process aborted.')
            return
        
        ''' Apply slow ramp until cavity is locked '''
        if not self.resonant():
            msg = 'PZT tuned within threshold. Ramping PZT to lock...'
#            print(msg)
            self.acquire_cavity_lock(span = self.parameters['Lock']['Sweep range'], step = self.parameters['Lock']['Sweep step size'], sweeps = self.sweeps)
        msg = 'Lock engaged with %f V transmission. Time to lock: %.1fs'%(self.cavity_transmission, time.time()-time0)
        print(msg)

        if self.abort:
            print('Locking process aborted.')
            return
        self.center_cavity_lock()
        self.locked = 1
        if self.abort:
            print('Locking process aborted.')
            self.locked = 0
            return
        self.parameters['Lock']['Frequency'] = self.get_frequency()
        self.parameters['PZT']['Setpoint'] = self.pzt
        self.save_setpoint()
        with open('lattice_frequency.txt', 'w') as file:
            file.write(str(self.get_frequency()))
        if hold:
#            print('Loop filter output centered. Engaging second integrator.')
            while self.resonant():
                self.center_cavity_lock(relative_gain = 0.1)
                if self.abort:
                    print('Locking process aborted.')
                    self.locked = 0
                    return
            print('Lost lock... reacquiring now.')
            self.locked = 0
            self.lock()
        
    def measure_linewidth(self):
        return
    
    def map_transmission(self, span, steps, f0 = None, delay = 0, filename = None, calibrate = True):
        ''' Measures and plots the cavity transmission around a span of f0 '''
#        if not self.calibrated:
        self.abort = 0
        if calibrate:
            self.calibrate_pzt()
        if f0 == None:
            self.lock(hold = False)
            f0 = self.get_frequency()
        self.disengage_gain()
        
#        f = np.linspace(f0-span/2, f0+span/2, steps)
        f = np.linspace(f0-span/2, f0+span/2, steps)
        V = self.convert_frequency_to_voltage(f)
        T = []
        print('Measuring cavity transfer function.')
        for v in V:
            self.actuate_pzt(v)
            time.sleep(delay)
            T.append(self.get_cavity_transmission())
#            print(v, T[-1])
            
        plt.semilogy((f-f0)*1000, T)
        ax = plt.gca()
        ax.set_xlabel('Detuning (MHz)')
        ax.set_ylabel('Cavity transmission (V)')
        
        ax2 = ax.twiny()
#        ax2.semilogy(V,T)
        ax2.set_xlabel('Voltage (V)')
        
        time.sleep(0.05)
        plt.show()
        
        if filename != None:
            with open(filename, 'w') as file:
                file.write('f0=%f\tspan=%f\tsteps=%i\tdelay=%fmax=%f\tmode frequency=%f\n'%(f0, span, steps, delay, np.max(T), f[np.argmax(T)]))
                file.write('Frequency\tPZT Voltage\tTransmission\n')
                for i in range(len(f)):
                    file.write('%f\t%f\t%f\n'%(V[i], f[i], T[i]))
                    
    def message(self, op, parameters, destination):
        ''' Sends a command to the destination, either "laser" or "PC" '''
        cmd = { "message": {"timestamp":astropy.time.Time.now().unix, "transmission_id": [1001],"op": op,"parameters": parameters }}
        if destination == 'laser':
            self.client.sendall(json.dumps(cmd).encode())
            reply = self.client.recv(1024) 
            return json.loads(reply)
        elif destination == 'PC':
            self.connection.sendall(json.dumps(cmd).encode())
            print(parameters)
    
    def oscillator(self, center, span, step):
        array = [center]
        j = 1
        while array[-1] < center+span/2 and array[-1] > center-span/2:
            sign = (j%2)*2-1
            for i in range(j+1):
                array.append(array[-1]-sign*step)
            step *= (j+1)/j
            j += 1
        return array
    
    def receive(self):
        reply = json.loads(self.sock.recv(1024).decode())
        print(reply)
        return reply
    
    def resonance_search(self):
        self.cavity_transmission = self.get_cavity_transmission()
        resonant = self.cavity_transmission > self.parameters['Lock']['Target voltage']
        return resonant or self.abort
    
    def unresonant(self):
        self.cavity_transmission = self.get_cavity_transmission()
        return self.cavity_transmission < self.parameters['Lock']['Target voltage']

    def resonant(self):
        self.cavity_transmission = self.get_cavity_transmission()
        check = self.cavity_transmission > self.parameters['Lock']['Target voltage']
        return check
    
    def save_setpoint(self):
        print('Saving settings to file.')
        with open('lattice_settings.txt', 'w') as file:
            json.dump(self.parameters, file)
        self.tab.update_setpoints(self.parameters)
        
    def server(self):
        self.cmds = {'stream_frequency':self.stream_frequency, 'lock':self.lock, 'tune_etalon':self.tune_etalon, 'tune_cavity':self.tune_cavity, 'ping':self.ping, 'set_cavity':self.actuate_pzt, 'acquire_etalon_lock':self.acquire_etalon_lock, 'acquire_cavity_lock':self.acquire_cavity_lock}
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server_address = ('0.0.0.0', 6666)
        sock.bind(server_address)
        print('Hosting server at %s:%i'%(server_address[0], server_address[1]))
        sock.listen(1)
        self.connection = None
        while True:
            # Wait for a connection
            try:
                if self.connection == None:
                    self.connection, client_address = sock.accept()
                    print('Connection from', client_address)
            except:
                continue
            try:
                data = self.connection.recv(1024)
                cmd = json.loads(data)
                if cmd['message']['op'] in ['data', 'abort']:
                    continue
                func = self.cmds.get(cmd['message']['op'])
                if cmd['message']['parameters'] == {}:
                    func()
                else:
                    print('Calling function ', func, ' with parameters ', cmd['message']['parameters'])
                    func(cmd['message']['parameters']) 
            except ConnectionResetError or json.JSONDecodeError:
                print('Connection aborted by client.')
                self.connection.close()
                continue

    def stop(self):
        return self.abort
    
    def stream_frequency(self):
        while True:
            reply = self.receive()
            f = self.get_frequency()
            if reply['message']['op'] == 'request':
                self.message(op='data', parameters = {'frequency':f, 'port':self.port}, destination = 'PC')
            elif reply['message']['op'] == 'done':
                return
        
    def tune_etalon(self, zoom = 1, threshold = None, quit_function = None):
        print('Tuning etalon...')
        if threshold == None:
            threshold = self.parameters['Etalon']['Tuning threshold']
        if quit_function == None:
            quit_function = self.stop
        X0 = self.etalon
#        X0 = self.convert_frequency_to_etalon(self.parameters['Lock']['Frequency'])
        x,c = optimize.line_search(x0 = X0, cost = self.cost, actuate = self.actuate_etalon, step = -zoom * self.parameters['Etalon']['Tuning step'], threshold = threshold, gradient = False, min_step = 0.01, full_output = True, quit_function = quit_function, fitting = False)
        self.etalon = x[-1]
        
#        ''' Automatic calibration step '''
#        f = np.array(c) + self.parameters['Lock']['Frequency']
#        x = np.array(x)
#        self.parameters['Etalon']['Slope'], self.parameters['Etalon']['Intercept'], r_value, p_value, std_err = stats.linregress(x, f)

        return x,c

    def tune_cavity(self, quit_function = None, output = False):
        ''' Estimate correct PZT position based on calibrated slope '''
        V0 = self.pzt
#        V0 = self.convert_frequency_to_voltage(self.parameters['Lock']['Frequency'])
        if quit_function == None:
            quit_function = self.stop
        x,c = optimize.line_search(x0 = V0, cost = self.cost, actuate = self.actuate_pzt, step = -self.parameters['PZT']['Tuning step'], threshold = self.parameters['PZT']['Tuning threshold'], gradient = False, min_step = 0.01, failure_threshold = self.parameters['Etalon']['Lock threshold'], quit_function = quit_function, x_max = 10, x_min = -10, full_output = True, output = output, fitting = False)
        self.pzt = x[-1]
        if self.abort:
            print('Cavity tuning process aborted.')
            return
        time.sleep(self.parameters['PZT']['Tuning delay']*5)
        if np.abs(self.cost()) > self.parameters['Etalon']['Lock threshold']:
            print('Etalon unlocked while tuning PZT; reacquiring etalon lock...')
            self.acquire_etalon_lock()
            self.tune_cavity()
        elif np.abs(self.cost()) > self.parameters['PZT']['Tuning threshold']:
            self.tune_cavity()
            
#        ''' Automatic calibration '''
#        f = np.array(c) + self.parameters['Lock']['Frequency']
#        x = np.array(x)
#        self.parameters['PZT']['Slope'], self.parameters['PZT']['Intercept'], r_value, p_value, std_err = stats.linregress(x, f)

    def warmup(self, threshold):
        self.abort = 0
        if self.check_etalon_lock():
            self.disengage_etalon_lock()
        self.disengage_gain()
        print('Beginning warmup procedure, threshold = %.0f GHz.'%threshold)
        while not self.abort:
            if np.abs(self.cost()) > threshold:
                self.tune_etalon(threshold = threshold)
        print('Warmup procedure aborted.')
        
class Setpoint():
    def __init__(self, name, tab, value, row, col, width = 1):
        self.tab = tab
        self.name = name
        self.label = self.tab._addLabel(self.name, row, col, width = width, style = self.tab.panel.styleUnlock, fontsize = 'S')
        self.value = self.tab._addEdit('%.3f'%value, row,col+1 + width-1)
        
    
        
class LatticeTab(gui.Tab):
    def __init__(self, panel, clock, folder, subfolder):
        super().__init__('Lattice', panel)
        self.panel = panel
        self.folder = folder
        self.subfolder = subfolder
        self.frequency = {}
        self.offset = 2082844800 - 3437602072
        
#        self.parameters = {}
#        self.parameters['Etalon'] = {'Tuning step':.1, 'Tuning delay': .1, 'Tuning threshold':.5, 'Lock threshold':1}
#        self.parameters['PZT'] = {'Tuning step': .75, 'Tuning delay': 0, 'Tuning threshold': 0.02}
#        self.parameters['Lock'] = {'Target voltage': 0.2, 'Sweep step size':.02, 'Sweep range': 0.5}
#        self.parameters['Slow'] = {'Gain': 0.01, 'Center threshold': .1}  
#        
        with open('lattice_settings.txt', 'r') as file:
            self.parameters = json.load(file)
        self.laser = MSquared(parameters = self.parameters, tab = self)
        
        self.setpoints = {}
        self.setpoints['Etalon'] = {}
        self.setpoints['PZT'] = {}
        self.setpoints['Lock'] = {}
        col = 0
        row = 0
        for x in ['Etalon']:
            self._addLabel(x, row, col, width = 1)
            row += 1
            for p in self.parameters[x]:
                self.setpoints[x][p] = Setpoint(p, self, self.parameters[x][p], row, col, width = 1)
                row += 1 
        col = 2
        row = 0
        for x in ['PZT']:
            self._addLabel(x, row, col, width = 1)
            row += 1
            for p in self.parameters[x]:
                self.setpoints[x][p] = Setpoint(p, self, self.parameters[x][p], row, col, width = 1)
                row += 1
        
        col = 4
        row = 0
        for x in ['Lock']:
            self._addLabel(x, row, col, width = 1)
            row += 1
            for p in self.parameters[x]:
                self.setpoints[x][p] = Setpoint(p, self, self.parameters[x][p], row, col, width = 1)
                row += 1
        
        self.warmup_button = self._addButton('Warmup', self.warmup, row+3, 0, style = self.panel.styleUnlock)
        self.lock_button = self._addButton('Lock', self.lock, row+3, 1, style = self.panel.styleUnlock)
        self.abort_button = self._addButton('Abort', self.abort, row+3, 2, style = self.panel.styleUnlock)
        self.status_button = self._addButton('Status', self.laser.get_system_status, row+3, 3, style = self.panel.styleUnlock)

#        self.calibrate_etalon_button = self._addButton('Calibrate etalon', self.calibrate_etalon, row+4, 0, style = self.panel.styleUnlock)
#        self.calibrate_pzt_button = self._addButton('Calibrate PZT', self.calibrate_pzt, row+4, 1, style = self.panel.styleUnlock)
        self.map_button = self._addButton('Map', self.map_transmission, row+3, 5, style = self.panel.styleUnlock)
#        self.center_button = self._addButton('Center PZT', self.laser.center_pzt, row+4, 2, style = self.panel.styleUnlock)
        self.calibrate_button = self._addButton('Calibrate', self.calibrate, row+3, 4, style = self.panel.styleUnlock)
        self.prepare_filepath()
        
    def update_setpoints(self, parameters):
        for x in parameters:
            for p in parameters[x]:
                self.setpoints[x][p].value.setText(str(parameters[x][p]))
        self.setLayout(self.layout)

    def abort(self):
        self.laser.abort = 1
        
    def calibrate(self):
        thread = Thread(target = self.laser.calibrate)
        thread.start()
        
    def calibrate_pzt(self):
        files = os.listdir(self.filepath['Calibration'])
        files = [x for x in files if 'pzt_calibration' in x]
        filename = self.filepath['Calibration'] + 'pzt_calibration_%i.txt'%(int(len(files)/2)+1)
        params = {"V0": self.laser.pzt, "span": 2, "steps": 30, "sweeps": 1, "delay": 0, "filename": filename}
        self.pzt_popup = gui.Popup('Calibrate PZT', params, function = self.laser.calibrate_pzt)
        self.pzt_popup.show()
        
    def calibrate_etalon(self):
        files = os.listdir(self.filepath['Calibration'])
        files = [x for x in files if 'etalon_calibration' in x]
        filename = self.filepath['Calibration'] + 'etalon_calibration_%i.txt'%(int(len(files)/2)+1)
        params = {"x0": self.laser.etalon, "span": 1, "steps": 25, "sweeps": 1, "delay": 0, "filename": filename}
        self.etalon_popup = gui.Popup('Calibrate etalon', params, function = self.laser.calibrate_etalon)
        self.etalon_popup.show()
        
    def lock(self):
        for x in self.parameters:
            for p in self.parameters[x]:
                self.parameters[x][p] = float(self.setpoints[x][p].value.text())
        self.laser.parameters = self.parameters
        self.thread = Thread(target=self.laser.lock)
        self.thread.start()
          
    def map_transmission(self):
        files = os.listdir(self.filepath['Calibration'])
        files = [x for x in files if 'mode_structure' in x]
        filename = 'mode_structure_%i.txt'%(len(files)+1)
        
        params = {"span": .05, "steps": 100, "f0": None, "delay": 0, "filename": filename}
        self.transmission_popup = gui.Popup('Map transmission', params)
        self.transmission_popup.show()
        
    def prepare_filepath(self):
        ''' Create file directory for the current day'''
        today = datetime.datetime.today().strftime('%y%m%d')
        self.directory = self.folder + today + '/' + self.subfolder

        for d in [self.folder + today, self.directory]:
            try:
                os.stat(d)
            except:
                os.mkdir(d) 
        self.filepath['Calibration'] = self.directory
            
    def warmup(self):
        threshold = 5
        self.thread = Thread(target = self.laser.warmup, args = (threshold,))
        self.thread.start()
        
        
if __name__ == '__main__':
    ''' Connect to MSquared laser '''
    app = QApplication(['Lattice laser controller'])
    folder = 'O:/Public/Yb clock/'
    subfolder = 'lattice/'
    panel = gui.Panel(app, clock = 'lattice', folder=folder, subfolder = subfolder)
    panel.filepath['Lattice'] = folder + 'pyClock2.0/lasers.json'
    panel.latticeTab = LatticeTab(panel, 'lattice', folder, subfolder)
    panel.loadTabs()
    panel.setFixedSize(1200,600)
    app.exec_()
    
#    panel.latticeTab.warmup()
    
    
    
    

    

#    m.server()
