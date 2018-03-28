import socket
from daq import MCDAQ
import json
import astropy.time

class Client():
    def __init__(self):
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = ('132.163.82.22', 6666)
        print('Connecting to %s port %s' % server_address)
        self.sock.connect(server_address)
    
        # connect to mcdaq
        params = {'device':'USB-2416', 'id':'1C2678C'}
#        self.daq = MCDAQ(params, function = 'input')
        
    def message(self, op, parameters = {}):
        ''' Sends a command to the server '''
        cmd = { "message": {"transmission_id": [1001],"op": op,"parameters": parameters }}
        self.sock.sendall(json.dumps(cmd).encode())
        return self.receive()
        
    def ping(self):
        reply = self.message(op='ping', parameters={'time': astropy.time.Time.now().unix})
        print(reply)
        
    def set_cavity(self, value):
        self.message(op='set_cavity', parameters = value)
        
    def receive(self):
        return json.loads(self.sock.recv(1024).decode())
    
    def tune_etalon(self):
        reply = self.message(op='tune_etalon')
        print(reply)
        
    def tune_cavity(self):
        reply = self.message(op='tune_cavity')
        print(reply)
        
    def lock(self):
        try:
#            cmd = { "message": {
#                    "transmission_id": [1001],
#                    "op": "lock",
#                    "parameters": {}}
#                  }
            # Send data
#            message = b'%f'%V
#            print('sending "%s"' % message)
            self.message(op='lock')
            
            while True:
#                reply = json.loads(self.sock.recv(1024).decode())
                reply = self.receive()
#                print(reply)
#                if reply == '':
#                    break
                print(reply['message']['msg'])
                if reply['message']['op'] == 'done':
                    break
            
            ''' Now start streaming data from the ADC '''
            while True:
                print('reading from ADC')
                V = self.daq.read(3)
                self.message(op='data', parameters = {'V':V})
                reply = self.receive()

                print(reply['message']['msg'])
                if reply['message']['op'] == 'done':
                    break
        finally:
            self.sock.close()
         
    def send(self, cmd):
        cmd = json.dumps(cmd).encode('ascii')
        self.sock.sendall(cmd)

if __name__ == '__main__':
    try:
        c
    except NameError:    
        c = Client()
    c.ping()
#    c.lock()
            