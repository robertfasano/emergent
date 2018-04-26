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
    def __init__(self, parameters):
        self.parameters = parameters
        
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
        
        self.etalon_lock = self.check_etalon_lock()
        if not self.etalon_lock or np.abs(self.cost()) > self.parameters['Etalon']['Lock threshold']:
            self.disengage_etalon_lock()
            self.actuate_etalon(self.setpoint['etalon'])
        self.actuate_pzt(self.setpoint['pzt'])
            
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

                if self.cavity_transmission > self.parameters['Acquisition']['Transmission threshold']:
                    print('Cavity transmission exceeds threshold; lock is engaged.')
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
                print('Retuning cavity to prevent drift.')
                self.tune_cavity(quit_function = self.resonant)

#            plt.figure()
#            plt.semilogy(v,t, '.')
#            plt.xlabel('Voltage')
#            plt.ylabel('Transmission')
#
#            time.sleep(.05)
#            plt.show()
            print('Sweep complete. Increasing range...')
                    
    def acquire_etalon_lock(self, zoom = 1, x = [], c = []):
        self.message(op = 'etalon_lock', parameters = {'operation': 'off'}, destination = 'laser')
        if self.abort:
            print('Aborting etalon lock.')
            return

        x0, c0 = self.tune_etalon(zoom = zoom)
        x.append(x0)
        c.append(c0)
        try:
            plt.figure()
            plt.plot(x,c)
            plt.xlabel('Etalon tune (%)')
            plt.ylabel(r'$f-f_0$')
            time.sleep(.05)
            plt.show()
        except ValueError:
            pass
        self.message(op = 'etalon_lock', parameters = {'operation': 'on'}, destination = 'laser')
        time.sleep(1)
        f = self.get_frequency()
        if np.abs(f-self.setpoint['frequency']) > self.parameters['Etalon']['Lock threshold'] and self.etalon_fail_count < self.max_etalon_fails:
            msg = 'Lock outside threshold at %f GHz, reacquiring...'%f
            print(msg)
            self.acquire_etalon_lock(zoom = 0.5, x = x, c = c)
            self.etalon_fail_count += 1
#        elif np.abs(f-self.setpoint['frequency']]) > self.parameters['Etalon']['Lock threshold'] and self.etalon_fail_count >= self.max_etalon_fails:
#            msg = 'Maximum etalon failures occurred, aborting locking routine.'
#            self.etalon_fail_count = 0
#            self.abort = 1
        else:
            msg = 'Etalon locked at f=%f GHz.'%f
            self.setpoint['etalon'] = self.etalon
            self.save_setpoint()
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
        
    def calibrate_pzt(self, V_min = -5, V_max = 5, steps = 50):
        ''' Calibrates the relationship between PZT voltage and frequency '''
        print('Calibrating PZT voltage - frequency curve.')
        self.disengage_gain()
        V = np.linspace(V_min, V_max, steps)
        f = []
        for v in V:
            self.actuate_pzt(v)
            time.sleep(0.01)
            f.append(self.get_frequency())
#            print(v, f[-1])
        V = np.delete(V,0)
        del f[0]
        plt.figure()
        plt.plot(V, f)
        plt.xlabel('DAC voltage (V)')
        plt.ylabel('Frequency')
        self.setpoint['pzt_slope'], self.setpoint['pzt_intercept'], r_value, p_value, std_err = stats.linregress(V, f)
        string = 'f = %f + %fV'%(self.setpoint['pzt_intercept'], self.setpoint['pzt_slope'])
        plt.title(string)
        time.sleep(0.05)
        plt.show()
        self.calibrated = 1

        self.save_setpoint()
        
    def center_cavity_lock(self, relative_gain = 1):
        self.pzt = optimize.line_search(x0 = self.pzt, cost = self.get_servo_output, actuate = self.actuate_pzt, step = self.parameters['Slow']['Gain'] * relative_gain, threshold = self.parameters['Slow']['Center threshold'], gradient = False, quit_function = self.unresonant) 

    def check_etalon_lock(self):
        reply = self.message(op='etalon_lock_status', parameters = {}, destination = 'laser')
        return {'on':1, 'off':0}[reply['message']['parameters']['condition']]

    def convert_frequency_to_voltage(self, f):
        ''' Returns a calibrated voltage V corresponding to a target frequency f '''
        if not self.calibrated:
            self.calibrate_pzt()
        return (f-self.setpoint['pzt_intercept'])/self.setpoint['pzt_slope']
    
    def convert_voltage_to_frequency(self, V):
        ''' Returns a calibrated frequency f corresponding to an input voltage V '''
        if not self.calibrated:
            self.calibrate_pzt()
        return self.setpoint['pzt_intercept'] + self.setpoint['pzt_slope'] * V
    
    def cost(self):
        return self.get_frequency()-self.setpoint['frequency']

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
        reply = self.message(op = 'etalon_lock', parameters = {'operation': 'off'}, destination = 'laser')
        print(reply)
    
    def load_setpoint(self):
        with open('lattice_settings.txt', 'r') as file:
            self.setpoint = json.load(file)
            
    def lock(self, hold = True, relock = False):
        print('Beginning lock routine.')
#        self.load_parameters()
        time0 = time.time()
        self.abort = 0
#        self.parameters = parameters    # an artifact of the two-PC architecture
#        self.actuate_pzt(self.pzt) 

        ''' Etalon locking '''
        self.etalon_lock = self.check_etalon_lock()
        
        if np.abs(self.cost()) > self.parameters['Etalon']['Lock threshold'] or not self.etalon_lock:
            self.disengage_gain() 
            print('Etalon unlocked; acquiring lock now... ')
            self.acquire_etalon_lock()
        if self.abort:
            print('Locking process aborted.')
            return
        
        ''' Tune near magic '''
        self.engage_gain('fast')
        if np.abs(self.cost()) > self.parameters['PZT']['Tuning threshold']:
            msg = 'Applying gain and tuning to target frequency.'
            print(msg)
            self.tune_cavity(quit_function = self.resonant, output = True)           # reset again in case adding gain shifted the frequency
        if self.abort:
            print('Locking process aborted.')
            return
        
        ''' Apply slow ramp until cavity is locked '''
        if not self.resonant():
            msg = 'PZT tuned within threshold. Ramping PZT to lock...'
            print(msg)
            self.acquire_cavity_lock(span = self.parameters['Acquisition']['Sweep range'], step = self.parameters['Acquisition']['Sweep step size'], sweeps = self.sweeps)
        msg = 'Lock engaged with %f V transmission. Time to lock: %.1fs'%(self.cavity_transmission, time.time()-time0)
        print(msg)

        if self.abort:
            print('Locking process aborted.')
            return
        
        self.center_cavity_lock()
        if self.abort:
            print('Locking process aborted.')
            return
        self.setpoint['frequency'] = self.get_frequency()
        self.setpoint['pzt'] = self.pzt
        self.save_setpoint()
        with open('lattice_frequency.txt', 'w') as file:
            file.write(str(self.get_frequency()))
        if hold:
            print('Loop filter output centered. Engaging second integrator.')
            while self.resonant():
                self.center_cavity_lock(relative_gain = 0.1)
                if self.abort:
                    print('Locking process aborted.')
                    return
            print('Lost lock... reacquiring now.')
            self.lock()
        
    def measure_linewidth(self):
        return
    
    def measure_transfer_function(self, span, steps, f0 = None):
        ''' Measures and plots the cavity transmission around a span of f0 '''
#        if not self.calibrated:
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
    
    def unresonant(self):
        self.cavity_transmission = self.get_cavity_transmission()
        return self.cavity_transmission < self.parameters['Acquisition']['Transmission threshold']

    def resonant(self):
        self.cavity_transmission = self.get_cavity_transmission()
        check = self.cavity_transmission > self.parameters['Acquisition']['Transmission threshold']
        return check
    
    def save_setpoint(self):
        with open('lattice_settings.txt', 'w') as file:
            json.dump(self.setpoint, file)
            
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
        x,c = optimize.line_search(x0 = self.etalon, cost = self.cost, actuate = self.actuate_etalon, step = -zoom * self.parameters['Etalon']['Tuning step'], threshold = threshold, gradient = False, min_step = 0.01, full_output = True, quit_function = quit_function)
        self.etalon = x[-1]
        return x,c

    def tune_cavity(self, quit_function = None, output = False):
        ''' Estimate correct PZT position based on calibrated slope '''
#        V0 = self.pzt
        V0 = self.convert_frequency_to_voltage(self.setpoint['frequency'])
        if quit_function == None:
            quit_function = self.stop
        x,c = optimize.line_search(x0 = V0, cost = self.cost, actuate = self.actuate_pzt, step = -self.parameters['PZT']['Tuning step'], threshold = self.parameters['PZT']['Tuning threshold'], gradient = False, min_step = 0.01, failure_threshold = self.parameters['Etalon']['Lock threshold'], quit_function = quit_function, x_max = 10, x_min = -10, full_output = True, output = output)
        self.pzt = x[-1]

            
        time.sleep(self.parameters['PZT']['Tuning delay']*5)
        if np.abs(self.cost()) > self.parameters['Etalon']['Lock threshold']:
            print('Etalon unlocked while tuning PZT; reacquiring etalon lock...')
            self.acquire_etalon_lock()
            self.tune_cavity()
        elif np.abs(self.cost()) > self.parameters['PZT']['Tuning threshold']:
            self.tune_cavity()
            
    def warmup(self, threshold):
        self.abort = 0
        self.etalon_lock = self.check_etalon_lock()
        if self.etalon_lock:
            self.message(op = 'etalon_lock', parameters = {'operation': 'off'}, destination = 'laser')
        print('Beginning warmup procedure, threshold = %.0f GHz.'%threshold)
        while not self.abort:
            if np.abs(self.cost()) > threshold:
                self.tune_etalon(threshold = threshold)
        print('Warmup procedure aborted.')
        
class Setpoint():
    def __init__(self, name, tab, value, row, col, width = 1):
        self.tab = tab
        self.name = name
        self.label = self.tab._addLabel(self.name, row, col, width = width, style = self.tab.panel.styleUnlock)
        self.value = self.tab._addEdit(str(value), row,col+1 + width-1)
        
class LatticeTab(gui.Tab):
    def __init__(self, panel, clock):
        super().__init__('Lattice', panel)
        self.panel = panel
        self.frequency = {}
        self.offset = 2082844800 - 3437602072
        
        self.parameters = {}
        self.parameters['Etalon'] = {'Tuning step':.1, 'Tuning delay': .1, 'Tuning threshold':.5, 'Lock threshold':1}
        self.parameters['PZT'] = {'Tuning step': .75, 'Tuning delay': 0, 'Tuning threshold': 0.02}
        self.parameters['Acquisition'] = {'Transmission threshold': 0.2, 'Sweep step size':.02, 'Sweep range': 0.5}
        self.parameters['Slow'] = {'Gain': 0.01, 'Center threshold': .1}  
        
        self.laser = MSquared(parameters = self.parameters)
        
        self.setpoints = {}
        self.setpoints['Etalon'] = {}
        self.setpoints['PZT'] = {}
        self.setpoints['Acquisition'] = {}
        self.setpoints['Slow'] = {}
        
        col = 0
        row = 0
        for x in ['Etalon', 'Slow']:
            self._addLabel(x, row, col, width = 1)
            row += 1
            for p in self.parameters[x]:
                self.setpoints[x][p] = Setpoint(p, self, self.parameters[x][p], row, col, width = 2)
                row += 1 
                
        col = 3
        row = 0
        for x in ['PZT', 'Acquisition']:
            self._addLabel(x, row, col, width = 1)
            row += 1
            for p in self.parameters[x]:
                self.setpoints[x][p] = Setpoint(p, self, self.parameters[x][p], row, col, width = 2)
                row += 1
        
        self._addButton('Warmup', self.warmup, row+3, 0, style = self.panel.styleUnlock)
        self._addButton('Lock', self.lock, row+3, 2, style = self.panel.styleUnlock)
        self._addButton('Map', self.measure_transfer_function, row+3, 1, style = self.panel.styleUnlock)
        self._addButton('Abort', self.abort, row+3, 3, style = self.panel.styleUnlock)
        
    def abort(self):
        self.laser.abort = 1
        
    def lock(self):
        for x in self.parameters:
            for p in self.parameters[x]:
                self.parameters[x][p] = float(self.setpoints[x][p].value.text())
        self.laser.parameters = self.parameters
        self.thread = Thread(target=self.laser.lock)
        self.thread.start()
          
    def measure_transfer_function(self):
        span = .05
        steps = 100
        self.laser.measure_transfer_function(span, steps, f0 = None)
        
    def warmup(self):
        threshold = 5
        self.thread = Thread(target = self.laser.warmup, args = (threshold,))
        self.thread.start()
        
if __name__ == '__main__':
    ''' Connect to MSquared laser and start server '''
    app = QApplication(['Lattice laser controller'])
    folder = 'O:/Public/Yb clock/'
    panel = gui.Panel(app, clock = 'lattice', folder=folder)
    panel.filepath['Lattice'] = folder + 'pyClock2.0/lasers.json'
    panel.latticeTab = LatticeTab(panel, 'lattice')
    panel.loadTabs()
    panel.setFixedSize(1100,600)
    app.exec_()
    
#    panel.latticeTab.warmup()
    
    

    

#    m.server()
