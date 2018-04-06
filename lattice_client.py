import socket
from labAPI import daq
import json
import astropy.time

class Client():
    def __init__(self, adc = None):
        # Create a TCP/IP socket
#        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        # connect to mcdaq
#        params = {'device':'USB-2416', 'id':'1C2678C'}

        if daq == None:
            params = {'device':'USB-2416', 'id':'1C26788'}
            self.daq = daq.MCDAQ(params, function = 'input')
        else: 
            self.daq = adc
        self.abort = 0
        self.transmission_id = 0
    def connect(self):
#        if not self.connected:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('132.163.82.22', 6666)
        self.sock.connect(server_address)
        self.connected = True
        print('Connected to %s port %s' % server_address)

        
    def message(self, op, parameters = {}):
        ''' Sends a command to the server '''
        if self.abort:
            cmd = { "message": {"transmission_id": [self.transmission_id],"op": 'abort',"parameters": parameters }}
        else:
            cmd = { "message": {"transmission_id": [self.transmission_id],"op": op,"parameters": parameters }}
        self.sock.sendall(json.dumps(cmd).encode())
        if op != 'data':
            print('Sent: ', cmd)
        return self.receive()
        
    def ping(self):
        if not self.connected:
            self.connect()
        reply = self.message(op='ping', parameters={'time': astropy.time.Time.now().unix})
        print(reply)

    def acquire_etalon_lock(self):
        self.message(op='acquire_etalon_lock')  
        
    def set_cavity(self, value):
        self.message(op='set_cavity', parameters = value)
        
    def receive(self):
        try:
            reply = json.loads(self.sock.recv(1024).decode())
            if reply['message']['op'] != 'request':
                print('Received: ', reply['message']['parameters'])
            self.transmission_id += 1
            return reply
        except ConnectionResetError:
            self.connected = False
            return -1
    
    def tune_etalon(self):
        reply = self.message(op='tune_etalon')
        print(reply)
        
    def tune_cavity(self):
        reply = self.message(op='tune_cavity')
        print(reply)
        
    def lock(self, parameters):
        self.abort = 0
        if not self.connected:
            self.connect()
        try:
            self.message(op='lock', parameters = parameters)
            
            ''' Begin listening mode for status updates during the etalon lock process '''
            while True:
                reply = self.receive()
                if reply == -1:
                    print('Connection closed by server.')
                    return
                if reply['message']['op'] == 'done':
                    break
            
            ''' When the etalon lock process is done, the server will send a 'done' message. Now start streaming data from the ADC. This is done by first requesting status from the server and responding with a voltage if needed. '''
            reply = self.receive()
            while True:
                if reply == -1:
                    print('Connection closed by server.')
                    return
                if reply['message']['op'] == 'request':
#                    V = self.daq.read(3)
                    transmission = self.daq.read(5)
                    output = self.daq.read(15)
                    reply = self.message(op='data', parameters = {'transmission':transmission, 'output':output})
                if reply == -1:
                    print('Connection closed by server.')
                    return
                if reply['message']['op'] == 'done':
                    break
        except KeyboardInterrupt:
            print('Locking routine aborted by user.')
#        self.sock.close()
        
    def send(self, cmd):
        cmd = json.dumps(cmd).encode('ascii')
        self.sock.sendall(cmd)

if __name__ == '__main__':
    try:
        c
    except NameError:    
        c = Client()
#    c.connect()
#    c.lock(parameters)
    
            