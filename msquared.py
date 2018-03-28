import json
import socket
import numpy as np
import time
import sys
import os
import astropy.time
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
from optimize import gradient_descent

class MSquared():
    def __init__(self, server, port, client):
        ''' Open socket connection '''
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.client.connect((server, port))
#        self.connect(client)
        self.message(op = 'start_link', parameters = {'ip_address': client}, destination='laser')

        ''' Connect to wavemeter '''
        self.wavemeter = bristol671.BristolWM('TCPIP::10.199.199.1::23::SOCKET')
        
        ''' Connect to DAC '''
        params = {'device':'USB-3105', 'id':'111696'}
        self.daq = MCDAQ(params, function = 'output')
        
        ''' Configure lock process settings '''
        self.delay = .1
        self.etalon = 41.96
        self.cavity_offset = 0
        self.increment = 3
        self.threshold = 1
        self.f0 = 394798.2
        
        self.etalon_lock = 0
        self.cavity_lock = 0
        
    def message(self, op, parameters, destination):
        ''' Sends a command to the destination, either "laser" or "PC" '''
        cmd = { "message": {"transmission_id": [1001],"op": op,"parameters": parameters }}
        if destination == 'laser':
            self.client.sendall(json.dumps(cmd).encode())
            reply = self.client.recv(1024) 
            return reply
        elif destination == 'PC':
            self.connection.sendall(json.dumps(cmd).encode())
            print(parameters)

    def acquireEtalonLock(self):
        self.message(op = 'etalon_lock', parameters = {'operation': 'off'}, destination = 'laser')
#        self.tuneEtalon(self.f0)
        self.tune('etalon')
        self.message(op = 'etalon_lock', parameters = {'operation': 'on'}, destination = 'laser')
        time.sleep(1)
        f = self.getFrequency()
        if np.abs(f-self.f0) > self.threshold:
            msg = 'Lock outside threshold at %f GHz, reacquiring...'%f
            self.message(op='update', parameters = msg, destination = 'PC')
            self.acquireEtalonLock()
        else:
            msg = 'Etalon locked at f=%f GHz.'%f
            self.message(op='update', parameters = msg, destination = 'PC')
            
#    def connect(self, client):
#        cmd = { "message": {
#                    "transmission_id": [1001],
#                    "op": "start_link",
#                    "parameters": { "ip_address": client } }
#              }
#        self.send(cmd)
#        self.message(op = 'start_link', parameters = {'ip_address': client})
#    
    def server(self):
        self.cmds = {'lock':self.lock, 'tune_etalon':self.tune_etalon, 'tune_cavity':self.tune_cavity, 'ping':self.ping, 'set_cavity':self.actuateCavityOffset}
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
            
        while True:
            data = self.connection.recv(1024)
            cmd = json.loads(data)
            func = self.cmds.get(cmd['message']['op'])
            if cmd['message']['parameters'] == {}:
                func()
            else:
                func(cmd['message']['parameters'])  
            self.message(op='done',  parameters = 'Successfully executed %s'%cmd['message']['op'], destination = 'PC')
#            finally:
        # Clean up the connection
        self.connection.close()
        
    def ping(self, parameters):
        latency = (-astropy.time.Time.now().unix+parameters['time'])*1000
        self.message(op='update', parameters = 'Ping: %.0f ms latency'%latency, destination = 'PC')
        
    def lock(self):
#        self.cavity_offset = 0
        self.daq.out(0, 10)        # trigger windowing to cut output
#        self.daq.out(6, self.cavity_offset)
        self.setCavityOffset(0)

        self.acquireEtalonLock()
        
        ''' Tune near magic '''
#        f0 = 394798.2
#        f = self.getFrequency()
#        sign = np.sign(f-f0)
#        
#        increment = .2
#        V = 0
#        while np.abs(f-f0) > .01:
#            oldSign = sign
#            self.daq.out(6, V)
#            time.sleep(1)
#            f = self.getFrequency()
#            print('f=%f, V=%f'%(f, V))
#            sign = np.sign(f-f0)
#            if sign != oldSign:
#                increment *= .5
#            V += sign*increment
#        V -= sign*increment
        self.tune('cavity')
        msg = 'PZT tuned to f=%f GHz.'%self.getFrequency()
        self.message(op='done', parameters = msg, destination = 'PC')
        
        ''' Apply slow ramp until cavity is locked '''
        time.sleep(3)
        msg = 'Attempting to lock...'
        self.message(op='update', parameters = msg, destination = 'PC')

        self.daq.out(0, 0)        # restore gain
        increment = 0.001
        rng = 0.075
        cavityTransmission = 0
        while cavityTransmission < 0.1:
            for x in np.arange(self.cavity_offset-rng/2, self.cavity_offset+rng/2, increment):
                self.daq.out(6, x)
                time.sleep(2)
                reply = self.connection.recv(1024).decode()
                reply = reply.split('}}}')[0] + '}}}'
                cavityTransmission = json.loads(reply)['message']['parameters']['V']
                msg = '%f V PZT; %f V cavity transmission'%(x, cavityTransmission)
                self.message(op='update', parameters = msg, destination = 'PC')
                if cavityTransmission > 0.1:
                    print('Target transmission hit!')
                    break

                
        ''' Apply full gain '''
        msg = 'Lock engaged.'
        self.message(op='done', parameters = msg, destination = 'PC')
        
    
#    def lockEtalon(self, state='on'):
#        cmd = { "message": {
#                "transmission_id": [1001],
#                "op": "etalon_lock",
#                "parameters": { "operation": state } }
#              }
#        self.send(cmd)
#        self.message(op = "etalon_lock", parameters = {"operation": state}, destination = "laser")
#        
#    def send(self, cmd):
#        cmd = json.dumps(cmd).encode('ascii')
#        self.client.sendall(cmd)
#        reply = self.client.recv(1024) #.decode()
#        return reply
    
    def actuateCavityOffset(self, value):
        self.cavity_offset = value
        self.daq.out(6, value)
        
    def actuateEtalon(self, value):
        self.etalon = value
        self.message(op = 'tune_etalon', parameters = {'setting': [self.etalon]}, destination = 'laser')

#        self.etalon = value
#        cmd = { "message": {
#                "transmission_id": [1001],
#                "op": "tune_etalon",
#                "parameters": { "setting": [self.etalon] } }
#              }
#        self.send(cmd)
        
    def tune_etalon(self):
        self.etalon = gradient_descent(x0 = self.etalon, cost = self.cost, actuator = self.actuateEtalon, dither = 0.1, gain = 1, threshold = 1)
    
    def tune_cavity(self):
        self.cavity_offset = gradient_descent(x0 = self.cavity_offset, cost = self.cost, actuator = self.actuateCavityOffset, dither = .025, gain = 1, threshold = .1)
            
    def tune(self, target):
        ''' Tunes the target (either etalon or cavity) to the specified frequency f0, within the range specified by self.threshold '''
        if target == 'etalon':
            self.etalon = gradient_descent(x0 = self.etalon, cost = self.cost, actuator = self.actuateEtalon, dither = 0.1, gain = 1, threshold = 1)
        
        elif target == 'cavity':
            self.cavity_offset = gradient_descent(x0 = self.cavity_offset, cost = self.cost, actuator = self.actuateCavityOffset, dither = .025, gain = 1, threshold = .1)
            
    def tuneEtalon(self, f0):
        f = self.getFrequency()
        sign = np.sign(f-f0)
        while np.abs(f-f0) > self.threshold:
            oldSign = sign
            self.etalon += sign*self.increment
            
#            self.setEtalon(self.etalon)
            self.message(op = 'tune_etalon', parameters = {'setting': [self.etalon]}, destination = 'laser')
            time.sleep(self.delay)
            f = self.getFrequency()
            
            sign = np.sign(f-f0)
            if sign != oldSign:
                self.increment *= .5
            
    def cost(self):
        return np.abs(self.getFrequency()-self.f0)
    
    def getFrequency(self):
        return self.wavemeter.frequency()*1000
    
#clientAddr = "192.168.1.120"
#if m == None:



''' Connect to MSquared laser and start server '''
server = "192.168.1.207"
port = 39933
client = "192.168.1.1"
m = MSquared(server, port, client)

m.server()
#




