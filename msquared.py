import json
import socket
import numpy as np
import time
import sys
import os
import astropy.time
from threading import Thread
from scipy import stats
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
from labAPI import daq, lattice_client, optimize
import bristol671     # note: this MUST be after mcdaq import, since bristol imports a different version
import matplotlib.pyplot as plt
plt.ion()
class MSquared():
    def __init__(self, server, port, client):
        ''' Open socket connection '''
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.client.connect((server, port))
        self.message(op = 'start_link', parameters = {'ip_address': client}, destination='laser')

        ''' Connect to wavemeter '''
        self.wavemeter = bristol671.BristolWM('TCPIP::10.199.199.1::23::SOCKET')
#        self.switch = BristolOFS()     # untested
        self.port = 0
#        self.switch.select(self.port)
        
        ''' Connect to DAC and ADC '''
        params = {'device':'USB-3105', 'id':'111696'}
        self.daq = daq.MCDAQ(params, function = 'output')
        
        params = {'device':'USB-2408', 'id':'1C96FD5'}
        self.adc = daq.MCDAQ(params, function = 'input', arange = 'BIP10VOLTS')
        

        ''' Configure lock process settings '''
        try:
            with open('etalon_settings.txt', 'r') as file:
                self.etalon = float(file.readlines()[0])
        except FileNotFoundError:
            self.etalon = 37
        self.cavity_offset = 0
        self.increment = 3
        self.threshold = 1
        try:
            with open('lattice_frequency.txt', 'r') as file:
                self.f0 = float(file.readlines()[0])
        except FileNotFoundError:
            self.f0 = 394798.23
        self.threads = {}
        self.etalon_lock = 0
        self.cavity_lock = 0
        self.cavity_offset = 0
        self.cavityTransmission = 0
        self.pzt_output = 0
        self.etalon_fail_count = 0
        self.max_etalon_fails = 5
        self.abort = 0
        self.sweeps = 5
            
    def oscillator(self, center, span, step):
        array = [center]
        j = 1
        while array[-1] < center+span/2 and array[-1] > center-span/2:
            sign = (j%2)*2-1
            for i in range(j):
                array.append(array[-1]-sign*step)
            step *= (j+1)/j
            j += 1
        return array
            
    def acquisition_cost(self):
        msg = {}
        self.message(op='request', parameters = msg, destination = 'PC')
        reply = self.connection.recv(1024).decode()
        reply = json.loads(reply.split('}}}')[0] + '}}}')    # make sure we only take the first json if multiple are sent
        print('Received reply ', reply)            
        if reply['message']['op'] == 'abort':
            return
        self.cavityTransmission = reply['message']['parameters']['transmission']
        self.pzt_output = reply['message']['parameters']['output']
        return self.parameters['Acquisition']['Transmission threshold'] - self.cavityTransmission
    
    def acquire_cavity_lock(self, span = 0.05, step = .001, sweeps = 5):
        ''' At this point, the etalon should be locked and the PZT should be tuned to magic. We now start sweeping the PZT
            in another thread while monitoring the transmission in this thread. Note that the one-way latency between computers
            is about 300 ms, so the sweep must be sufficiently slow to allow locking at the right frequency.'''
#        bestT = 0
#        for i in range(sweeps):
        while True:
            X = self.oscillator(self.cavity_offset, span, step)
            t = []
            v = []
            o = []
            f = []
            left_points = []
            right_points = []
            peak_found = False
            count = 0
            for x in X:
                self.cavityTransmission = self.get_cavity_transmission()
                self.pzt_output = self.get_servo_output()
                
                f.append(self.cost())
                t.append(self.cavityTransmission)
                v.append(x)
                o.append(self.pzt_output)
                if count > span/step:
                    slope, intercept, r_value, p_value, std_err = stats.linregress(v,t)
                    z0 = 5
                    if np.abs(slope/std_err) > z0:
                        print('Slope detected! %f +/- %f'%(slope, std_err))
                        self.actuateCavityOffset(v[np.argmax(t)])
                        break

                ''' If an outlier is detected, take a closer look '''
                if self.cavityTransmission > self.parameters['Acquisition']['Transmission threshold']:
                    print('Cavity transmission exceeds threshold; lock is engaged.')
                    return
                
                if np.std(t) != 0:
                    z = (np.max(t) - np.mean(t))/np.std(t)
                    threshold = 5
                    if z>threshold: #and count > steps/2:
                        fmax = f[np.argmax(t)]
                        ''' We have just stepped onto a peak '''
                        print('%f-sigma peak detected at  %f (sigma = %f).'%(z, fmax, np.std(t)))
                        peak_found = True
                        factor = 2/np.abs(z)
                        span *= factor
                        print('Recentering at ', fmax, ' with span decreased by a factor of ', z/2.5)
                        self.actuateCavityOffset(v[np.argmax(t)])
                        break
                count += 1

                self.actuateCavityOffset(x)
            if not peak_found:
                self.actuateCavityOffset(v[np.argmax(t)])
                span *= 1.25
            if np.abs(self.cost()) > .015:
                print('Retuning cavity to prevent drift.')
                self.tune_cavity(quit_function = self.resonant)

            print('Sweep complete. Increasing range...')
            plt.plot(v,t, '.')
            plt.xlabel('Voltage')
            plt.ylabel('Transmission')

            time.sleep(.5)
            plt.show()
                    
    def acquire_etalon_lock(self, zoom = 1):
        self.message(op = 'etalon_lock', parameters = {'operation': 'off'}, destination = 'laser')
        self.tune_etalon(zoom = zoom)
        self.message(op = 'etalon_lock', parameters = {'operation': 'on'}, destination = 'laser')
        time.sleep(1)
        f = self.get_frequency()
        if np.abs(f-self.f0) > self.parameters['Etalon']['Lock threshold'] and self.etalon_fail_count < self.max_etalon_fails:
            msg = 'Lock outside threshold at %f GHz, reacquiring...'%f
            self.message(op='update', parameters = msg, destination = 'PC')
            self.acquire_etalon_lock(zoom = 0.5)
            self.etalon_fail_count += 1
#        elif np.abs(f-self.f0) > self.parameters['Etalon']['Lock threshold'] and self.etalon_fail_count >= self.max_etalon_fails:
#            msg = 'Maximum etalon failures occurred, aborting locking routine.'
#            self.message(op='update', parameters = msg, destination = 'PC')
#            self.etalon_fail_count = 0
#            self.abort = 1
        else:
            msg = 'Etalon locked at f=%f GHz.'%f
            with open('etalon_settings.txt', 'w') as file:
                file.write(str(self.etalon))
            self.message(op='update', parameters = msg, destination = 'PC')
            self.etalon_fail_count = 0

    def actuateCavityOffset(self, value):
        self.cavity_offset = value
        self.daq.out(6, value)
        time.sleep(self.parameters['PZT']['Tuning delay'])
        return self.get_frequency()
        
    def actuateEtalon(self, value):
        self.etalon = value
        self.message(op = 'tune_etalon', parameters = {'setting': [self.etalon]}, destination = 'laser')
        time.sleep(self.parameters['Etalon']['Tuning delay'])
        return self.get_frequency()
    
    def get_pzt_output(self):
        msg = "{'V':%f, 'Transmission':%f, 'Output':%f}"%(self.cavity_offset, self.cavityTransmission, self.pzt_output)
        self.message(op='request', parameters = msg, destination = 'PC')
        reply = self.connection.recv(1024).decode()
        reply = json.loads(reply.split('}}}')[0] + '}}}')    # make sure we only take the first json if multiple are sent
        if reply['message']['op'] == 'abort':
            self.abort = 1
            return 999
        self.cavityTransmission = reply['message']['parameters']['transmission']
        self.pzt_output = reply['message']['parameters']['output']
        return self.pzt_output

        
    def center_cavity_lock(self, relative_gain = 1):
        self.cavity_offset = optimize.line_search(x0 = self.cavity_offset, cost = self.get_servo_output, actuate = self.actuateCavityOffset, step = self.parameters['Slow']['Gain'] * relative_gain, threshold = self.parameters['Slow']['Center threshold'], gradient = False, quit_function = self.unresonant) 

    def check_etalon_lock(self):
        reply = self.message(op='etalon_lock_status', parameters = {}, destination = 'laser')
        return {'on':1, 'off':0}[reply['message']['parameters']['condition']]

    def cost(self):
        return self.get_frequency()-self.f0

    def get_cavity_transmission(self):
        return self.adc.read(0)

    def get_servo_output(self):
        return self.adc.read(1)
    
    def get_frequency(self, window = 1):
        v = []
        for i in range(window):
            v.append(self.wavemeter.frequency()*1000)
        return np.mean(v)
    
    def servo_etalon(self, parameters):
        self.parameters = parameters
        while True:
            self.tune_etalon()
            
    def lock(self, parameters):
        self.abort = 0
        self.parameters = parameters
        
        self.daq.out(13,10)             # send +10V to windowing inputs of loop filters to cut output
        self.daq.out(0, 10)        
        self.actuateCavityOffset(self.cavity_offset) 
        
        self.etalon_lock = self.check_etalon_lock()
        
        if np.abs(self.cost()) > self.parameters['Etalon']['Lock threshold'] or not self.etalon_lock:
            self.acquire_etalon_lock()
        if self.abort:
            print('Aborted by client after etalon lock')
            return
        print('Tuning PZT near target frequency...')
        ''' Tune near magic '''
        msg = 'Applying gain and tuning to target frequency.'

        self.message(op='update', parameters = msg, destination = 'PC')
        self.daq.out(0, 0)        # restore gain
        self.tune_cavity(quit_function = self.resonant)           # reset again in case adding gain shifted the frequency
        
        msg = 'PZT tuned to f=%f GHz. Ramping PZT to lock...'%self.get_frequency()
        self.message(op='done', parameters = msg, destination = 'PC')
        
        ''' Apply slow ramp until cavity is locked '''
        self.acquire_cavity_lock(span = self.parameters['Acquisition']['Sweep range'], step = self.parameters['Acquisition']['Sweep step size'], sweeps = self.sweeps)
        msg = 'Lock engaged with %f V transmission. Centering output...'%self.cavityTransmission
        self.message(op='request', parameters = msg, destination = 'PC')
        with open('lattice_frequency.txt', 'w') as file:
            file.write(str(self.get_frequency()))
        self.center_cavity_lock()
        print('Centered loop filter output.')
        print('Engaging second integrator.')
        while self.resonant():
            self.center_cavity_lock(relative_gain = 0.1)
        
        print('Lost lock... reacquiring now.')
        self.lock(self.parameters)
            
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
    
    def ping(self, parameters):
        self.latency = (astropy.time.Time.now().unix-parameters['time'])*1000
        self.message(op='update', parameters = 'Ping: %.0f ms latency'%self.latency, destination = 'PC')

 
    def receive(self):
        reply = json.loads(self.sock.recv(1024).decode())
        print(reply)
        return reply
    
    def unresonant(self):
        return self.get_cavity_transmission() < self.parameters['Acquisition']['Transmission threshold']

    def resonant(self):
        return self.get_cavity_transmission() > self.parameters['Acquisition']['Transmission threshold']
    
    def server(self):
        self.cmds = {'stream_frequency':self.stream_frequency, 'lock':self.lock, 'tune_etalon':self.tune_etalon, 'tune_cavity':self.tune_cavity, 'ping':self.ping, 'set_cavity':self.actuateCavityOffset, 'acquire_etalon_lock':self.acquire_etalon_lock, 'acquire_cavity_lock':self.acquire_cavity_lock}
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

    def stream_frequency(self):
        while True:
            reply = self.receive()
            f = self.get_frequency()
            if reply['message']['op'] == 'request':
                self.message(op='data', parameters = {'frequency':f, 'port':self.port}, destination = 'PC')
            elif reply['message']['op'] == 'done':
                return
        
    def tune_etalon(self, zoom = 1):
        self.etalon = optimize.line_search(x0 = self.etalon, cost = self.cost, actuate = self.actuateEtalon, step = -zoom * self.parameters['Etalon']['Tuning step'], threshold = self.parameters['Etalon']['Tuning threshold'], gradient = False, min_step = 0.01)
        
    def tune_cavity(self, quit_function = None):
        self.cavity_offset = optimize.line_search(x0 = self.cavity_offset, cost = self.cost, actuate = self.actuateCavityOffset, step = -self.parameters['PZT']['Tuning step'], threshold = self.parameters['PZT']['Tuning threshold'], gradient = False, min_step = 0.01, failure_threshold = 2*self.parameters['Etalon']['Lock threshold'], quit_function = quit_function, x_max = 10, x_min = -10)
        time.sleep(self.parameters['PZT']['Tuning delay']*5)
        if np.abs(self.cost()) > self.parameters['Etalon']['Lock threshold']:
            print('Etalon unlocked while tuning PZT; reacquiring etalon lock...')
            self.acquire_etalon_lock()
            self.tune_cavity()
        elif np.abs(self.cost()) > self.parameters['PZT']['Tuning threshold']:
            self.tune_cavity()

if __name__ == '__main__':
    ''' Connect to MSquared laser and start server '''
    server = "192.168.1.207"
    port = 39933
    client = "192.168.1.1"
    m = MSquared(server, port, client)
    m.daq.out(0,0)
    m.daq.out(6,0)
    m.daq.out(13,0)
#    m.lock()
    m.server()
