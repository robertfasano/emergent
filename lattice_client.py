import socket
from daq import MCDAQ
import json
import astropy.time

class Client():
    def __init__(self):
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
        # connect to mcdaq
#        params = {'device':'USB-2416', 'id':'1C2678C'}
        params = {'device':'USB-2416', 'id':'1C26788'}

        self.daq = MCDAQ(params, function = 'input')
        
    def connect(self):
        server_address = ('132.163.82.22', 6666)
        print('Connecting to %s port %s' % server_address)
        self.sock.connect(server_address)
        
    def message(self, op, parameters = {}):
        ''' Sends a command to the server '''
        cmd = { "message": {"transmission_id": [1001],"op": op,"parameters": parameters }}
        self.sock.sendall(json.dumps(cmd).encode())
        if op != 'data':
            print('Sent: ', cmd)
        return self.receive()
        
    def ping(self):
        reply = self.message(op='ping', parameters={'time': astropy.time.Time.now().unix})
        print(reply)
        
    def acquire_etalon_lock(self):
        self.message(op='acquire_etalon_lock')  
        
    def set_cavity(self, value):
        self.message(op='set_cavity', parameters = value)
        
    def receive(self):
        reply = json.loads(self.sock.recv(1024).decode())
        if reply['message']['op'] != 'request':
            print('Received: ', reply['message']['parameters'])
        return reply
    
    def tune_etalon(self):
        reply = self.message(op='tune_etalon')
        print(reply)
        
    def tune_cavity(self):
        reply = self.message(op='tune_cavity')
        print(reply)
        
    def lock(self, parameters):
        try:
            self.message(op='lock', parameters = parameters)
            
            ''' Begin listening mode for status updates during the etalon lock process '''
            while True:
                reply = self.receive()
                if reply['message']['op'] == 'done':
                    break
            
            ''' When the etalon lock process is done, the server will send a 'done' message. Now start streaming data from the ADC. This is done by first requesting status from the server and responding with a voltage if needed. '''
            reply = self.receive()
            while True:
                if reply['message']['op'] == 'request':
#                    V = self.daq.read(3)
                    transmission = self.daq.read(5)
                    output = self.daq.read(15)
                    reply = self.message(op='data', parameters = {'transmission':transmission, 'output':output})

                if reply['message']['op'] == 'done':
                    break
        except KeyboardInterrupt:
            print('Locking routine aborted by user.')
         
    def send(self, cmd):
        cmd = json.dumps(cmd).encode('ascii')
        self.sock.sendall(cmd)

if __name__ == '__main__':
    try:
        c.connect()
    except NameError:    
        c = Client()
#    c.ping()
    parameters = {'pzt_center_gain':.0002, 'cavity_tune_delay':.5, 'sweep_steps':60, 'cavity_tune_threshold':.02, 'cavity_transmission_threshold':0.1, 'pzt_center_threshold':.3}
    c.lock(parameters)
    
            