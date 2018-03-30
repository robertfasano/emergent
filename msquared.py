import json
import socket
import numpy as np
import time
import sys
import os
import astropy.time
from threading import Thread
import matplotlib.pyplot as plt
plt.ion()
try:
    sys.path.remove('C:\\ProgramData\\Anaconda3\\lib\\site-packages\\mcdaq-1-py3.6.egg')
except ValueError:
    pass
if os.name == 'posix':        # if using OS X, open a special testing version of the program
    sys.path.append('/Users/rjf2/Documents/GitHub')
else:
#    sys.path.append('C:\\Users\\Public\\Documents\\GitHub')
#    sys.path.append('C:\\Users\\Robbie\\Documents\\GitHub')
    sys.path.insert(0, 'C:\\Users\\yblab\\Python\\mcdaq')

    sys.path.append('O:\\Public\\Yb clock')
#    import mcdaq
import bristol671     # note: this MUST be after mcdaq import, since bristol imports a different version

from daq import MCDAQ
from optimize import line_search

class MSquared():
    def __init__(self, server, port, client):
        ''' Open socket connection '''
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.client.connect((server, port))
        self.message(op = 'start_link', parameters = {'ip_address': client}, destination='laser')

        ''' Connect to wavemeter '''
        self.wavemeter = bristol671.BristolWM('TCPIP::10.199.199.1::23::SOCKET')
        
        ''' Connect to DAC '''
        params = {'device':'USB-3105', 'id':'111696'}
        self.daq = MCDAQ(params, function = 'output')
        
        ''' Configure lock process settings '''
        self.etalon = 46.96
        self.cavity_offset = 0
        self.increment = 3
        self.threshold = 1
        self.f0 = 394798.24
        self.threads = {}
        self.etalon_lock = 0
        self.cavity_lock = 0
        self.cavityTransmission = 0
        self.pzt_output = 0
        
        self.cavity_transmission_threshold = 0.5
        self.etalon_tune_step = 1
        self.cavity_tune_step = .1
        self.etalon_tune_delay = 1
        self.cavity_tune_delay = .6
        self.etalon_tune_threshold = .01
        self.etalon_lock_threshold = 1.5
        self.cavity_tune_threshold = .02
        self.sweep_range = self.cavity_tune_threshold * 2
        self.sweep_steps = 50
        self.num_sweeps = 5
        
    def message(self, op, parameters, destination):
        ''' Sends a command to the destination, either "laser" or "PC" '''
        cmd = { "message": {"timestamp":astropy.time.Time.now().unix, "transmission_id": [1001],"op": op,"parameters": parameters }}
        if destination == 'laser':
            self.client.sendall(json.dumps(cmd).encode())
            reply = self.client.recv(1024) 
            return reply
        elif destination == 'PC':
            self.connection.sendall(json.dumps(cmd).encode())
            print(parameters)
            
    def receive(self):
        reply = json.loads(self.sock.recv(1024).decode())
        print(reply)
        return reply
    
    def acquireEtalonLock(self):
        self.message(op = 'etalon_lock', parameters = {'operation': 'off'}, destination = 'laser')
        self.tune_etalon()
        self.message(op = 'etalon_lock', parameters = {'operation': 'on'}, destination = 'laser')
        time.sleep(1)
        f = self.getFrequency()
        if np.abs(f-self.f0) > self.etalon_lock_threshold:
            msg = 'Lock outside threshold at %f GHz, reacquiring...'%f
            self.message(op='update', parameters = msg, destination = 'PC')
            self.acquireEtalonLock()
        else:
            msg = 'Etalon locked at f=%f GHz.'%f
            self.message(op='update', parameters = msg, destination = 'PC')
            
    def server(self):
        self.cmds = {'lock':self.lock, 'tune_etalon':self.tune_etalon, 'tune_cavity':self.tune_cavity, 'ping':self.ping, 'set_cavity':self.actuateCavityOffset, 'acquire_etalon_lock':self.acquireEtalonLock, 'acquire_cavity_lock':self.acquire_cavity_lock}
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server_address = ('0.0.0.0', 6666)
        sock.bind(server_address)
        print('Hosting server at %s:%i'%(server_address[0], server_address[1]))
        sock.listen(1)

        while True:
            # Wait for a connection
            try:
                self.connection, client_address = sock.accept()
                print('Connection from', client_address)
                break
            except:
                continue
            

            data = self.connection.recv(1024)
            cmd = json.loads(data)
            func = self.cmds.get(cmd['message']['op'])
            self.message(op='confirmation',parameters = 'Running %s function'%func, destination = 'PC')
            if cmd['message']['parameters'] == {}:
                func()
            else:
                print('Calling function with parameters ', cmd['message']['parameters'])
                func(cmd['message']['parameters'])  
#            self.message(op='done',  parameters = 'Successfully executed %s'%cmd['message']['op'], destination = 'PC')
#            finally:
        # Clean up the connection
            self.connection.close()
        
    def ping(self, parameters):
        self.latency = (-astropy.time.Time.now().unix+parameters['time'])*1000
        self.message(op='update', parameters = 'Ping: %.0f ms latency'%self.latency, destination = 'PC')
        
    def lock(self, parameters):
        self.cavity_tune_delay = parameters['cavity_tune_delay']
        self.sweep_steps = parameters['sweep_steps']
        self.cavity_tune_threshold = parameters['cavity_tune_threshold']
        self.cavity_transmission_threshold = parameters['cavity_transmission_threshold']
        self.pzt_center_threshold = parameters['pzt_center_threshold']
        self.pzt_center_gain = parameters['pzt_center_gain']
            
        self.daq.out(13,10)             # send +10V to windowing inputs of loop filters to cut output
        self.daq.out(0, 10)        
        self.actuateCavityOffset(0) 
        
        self.etalon_lock = self.check_etalon_lock()
        
        if np.abs(self.cost()) > self.etalon_lock_threshold:
            self.acquireEtalonLock()
        self.message(op = 'etalon_lock', parameters = {'operation': 'on'}, destination = 'laser') # send an extra lock signal to prevent human input on the GUI from changing this

        ''' Tune near magic '''
        self.tune_cavity()    
        msg = 'PZT tuned to f=%f GHz. Applying gain...'%self.getFrequency()
        self.message(op='update', parameters = msg, destination = 'PC')
        self.daq.out(0, 0)        # restore gain
        self.tune_cavity()           # reset again in case adding gain shifted the frequency

        msg = 'PZT tuned to f=%f GHz. Ramping PZT to lock...'%self.getFrequency()
        self.message(op='done', parameters = msg, destination = 'PC')
        
        ''' Apply slow ramp until cavity is locked '''
        time.sleep(3)
        
        self.acquire_cavity_lock(span = self.sweep_range, steps = self.sweep_steps, sweeps = self.num_sweeps)
        msg = 'Lock engaged with %f V transmission. Centering output...'%self.cavityTransmission
        self.message(op='request', parameters = msg, destination = 'PC')
        self.center_cavity_lock()
        




        
    def check_etalon_lock(self):
        reply = self.message(op='etalon_lock_status', parameters = {}, destination = 'laser')
        print(reply)
        
    def center_cavity_lock(self):
        while True:
            msg = "{'V':%f, 'Transmission':%f, 'Output':%f}"%(self.cavity_offset, self.cavityTransmission, self.pzt_output)
            self.message(op='request', parameters = msg, destination = 'PC')
            reply = self.connection.recv(1024).decode()
            reply = reply.split('}}}')[0] + '}}}'    # make sure we only take the first json if multiple are sent
            self.cavityTransmission = json.loads(reply)['message']['parameters']['transmission']
            self.pzt_output = json.loads(reply)['message']['parameters']['output']
            
            self.actuateCavityOffset(self.cavity_offset - self.pzt_center_gain * self.pzt_output)
            
            if self.pzt_output < self.pzt_center_threshold:
                break
            
            elif self.cavityTransmission < self.cavity_transmission_threshold:
                msg = 'Recentering failed...'
                self.message(op='done', parameters = msg, destination = 'PC')
                return
        print('engaging slow lock!')
        self.daq.out(13,0)      # engage slow lock
        
        time.sleep(3)
        print('re-testing lock status')
        while True:
            time.sleep(0.5)
            msg = "{'V':%f, 'Transmission':%f, 'Output':%f}"%(self.cavity_offset, self.cavityTransmission, self.pzt_output)
            self.message(op='request', parameters = msg, destination = 'PC')
            reply = self.connection.recv(1024).decode()
            reply = reply.split('}}}')[0] + '}}}'    # make sure we only take the first json if multiple are sent
            self.cavityTransmission = json.loads(reply)['message']['parameters']['transmission']
            self.pzt_output = json.loads(reply)['message']['parameters']['output']
                        
            if self.pzt_output < self.pzt_center_threshold:
                msg = 'Lock acquired!'
                self.message(op='done', parameters = msg, destination = 'PC')
                return
            
            elif self.cavityTransmission < self.cavity_transmission_threshold:
                msg = 'Slow lock failed...'
                self.message(op='done', parameters = msg, destination = 'PC')
                return

    def acquire_cavity_lock(self, span = 0.05, steps = 200, sweeps = 5):
        ''' At this point, the etalon should be locked and the PZT should be tuned to magic. We now start sweeping the PZT
            in another thread while monitoring the transmission in this thread. Note that the one-way latency between computers
            is about 300 ms, so the sweep must be sufficiently slow to allow locking at the right frequency.'''
#        sweep_thread = Thread(target=self.sweep_PZT, args=(span, steps, delay))
#        self.threads['Sweep'] = 1
#        sweep_thread.start()
        bestT = 0
        t = []
        v = []
        for i in range(sweeps):
#            msg = 'Beginning sweep %i with center voltage %f and span %f'%(i, self.cavity_offset, span)
#            self.message(op='update', parameters = msg, destination = 'PC')
            
            X = np.linspace(self.cavity_offset-span/2, self.cavity_offset+span/2, steps)
            X = np.append(X[X>=self.cavity_offset],X[X<self.cavity_offset])
    #        while self.threads['Sweep']:
            for x in X:
                msg = "{'Sweep':%i,'V':%f, 'Transmission':%f, 'Output':%f}"%(i,x, self.cavityTransmission, self.pzt_output)
                self.message(op='request', parameters = msg, destination = 'PC')
                reply = self.connection.recv(1024).decode()
                reply = reply.split('}}}')[0] + '}}}'    # make sure we only take the first json if multiple are sent
                self.cavityTransmission = json.loads(reply)['message']['parameters']['transmission']
                self.pzt_output = json.loads(reply)['message']['parameters']['output']

                t.append(self.cavityTransmission)
                v.append(x)
                if self.cavityTransmission > self.cavity_transmission_threshold:
#                    plt.plot(v,t)
#                    plt.pause(0.05)
                    return
                self.actuateCavityOffset(x)
#                msg = '%f GHz; %f V cavity transmission'%(f, self.cavityTransmission)
#                self.message(op='update', parameters = msg, destination = 'PC')

            if np.max(t) > bestT:
                bestT = np.max(t)
                bestV = v[np.argmax(t)]
            self.actuateCavityOffset(bestV)
            factor = .75
            span *= factor
            self.cavity_tune_delay /= factor
#            steps = int(steps*factor)
            
        plt.plot(v,t)
        plt.pause(0.05)

        
#        while self.cavityTransmission < 0.05:
#            reply = self.connection.recv(1024).decode()
#            reply = reply.split('}}}')[0] + '}}}'    # make sure we only take the first json if multiple are sent
#            self.cavityTransmission = json.loads(reply)['message']['parameters']['V']
#            msg = '%f GHz; %f V cavity transmission'%(self.getFrequency(), cavityTransmission)
#            self.message(op='update', parameters = msg, destination = 'PC')
#            if self.cavityTransmission > 0.05:
#                self.threads['Sweep'] = 0
#                print('Target transmission hit!')
            
#    def sweep_PZT(self, span, steps, delay):
#        sign = -np.sign(self.getFrequency()-self.f0)
#        print('Starting sweep frequency: ', self.getFrequency())
#        step = .1         # first guess for step size; this will be calibrated by the sweep after it completes one period
#        while self.threads['Sweep']:
#            f = self.actuateCavityOffset(self.cavity_offset + sign * step, delay = 1)
#            print('sign: ', sign, ' ', self.cavity_offset, ' V = ', f, ' GHz')
#            if f >= self.f0 + span/2:
#                sign = -1
#                V_upper = self.cavity_offset
#            elif f <= self.f0 - span/2:
#                sign = 1
#                V_lower = self.cavity_offset
#                step = (V_upper - V_lower)/steps
#                

    def sweep_PZT(self, span, steps, delay):
        X = np.linspace(self.cavity_offset-span/2, self.cavity_offset+span/2, steps)
        X = np.append(X[X>=self.cavity_offset],X[X<self.cavity_offset])
        
        t = []
        v = []
#        while self.threads['Sweep']:
        for x in X:
            t.append(self.cavityTransmission)
            v.append(x)
            f = self.actuateCavityOffset(x)
            print(x, ' V = ', f, ' GHz')
#        plt.plot(v,t)
#        plt.pause(0.05)
            
    def actuateCavityOffset(self, value):
        self.cavity_offset = value
        self.daq.out(6, value)
        time.sleep(self.cavity_tune_delay)
        return self.getFrequency()
        
    def actuateEtalon(self, value):
        self.etalon = value
        self.message(op = 'tune_etalon', parameters = {'setting': [self.etalon]}, destination = 'laser')
        time.sleep(self.etalon_tune_delay)
        return self.getFrequency()
        
    def tune_etalon(self):
        self.etalon = line_search(x0 = self.etalon, cost = self.cost, actuate = self.actuateEtalon, step = self.etalon_tune_step, threshold = self.etalon_tune_threshold)
    
    def tune_cavity(self):
        self.cavity_offset = line_search(x0 = self.cavity_offset, cost = self.cost, actuate = self.actuateCavityOffset, step = self.cavity_tune_step, threshold = self.cavity_tune_threshold)
        time.sleep(self.cavity_tune_delay)
        if np.abs(self.cost()) > self.cavity_tune_threshold:
            self.tune_cavity()
            
    def cost(self):
        return self.getFrequency()-self.f0
    
    def getFrequency(self):
        return self.wavemeter.frequency()*1000

''' Connect to MSquared laser and start server '''
server = "192.168.1.207"
port = 39933
client = "192.168.1.1"
m = MSquared(server, port, client)
m.daq.out(0,0)
m.daq.out(6,0)
m.daq.out(13,0)

m.server()

#m.acquireEtalonLock()
#




