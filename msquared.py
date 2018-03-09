import json
import socket
import bristol671
import numpy as np

class MSquared():
    def __init__(self, server, port, client):
        ''' Open socket connection '''
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.client.connect((server, port))
        self.connect(client)
        
        self.wavemeter = bristol671.BristolWM('TCPIP::10.199.199.1::23::SOCKET')
        
    def acquireEtalonLock(self):
        f0 = 394798.2
        self.tuneEtalon(f0)
        self.lockEtalon(state='on')
        f = self.getFrequency()
        if np.abs(f-f0) > 5:
            print('Lock failed, reacquiring...')
            self.acquireEtalonLock()
        else:
            print('Etalon locked at f=%f GHz.'%f)
            
    def connect(self, client):
        cmd = { "message": {
                    "transmission_id": [1001],
                    "op": "start_link",
                    "parameters": { "ip_address": client } }
              }
        
        self.send(cmd)
    
    def lockEtalon(self, state='on'):
        cmd = { "message": {
                "transmission_id": [1001],
                "op": "etalon_lock",
                "parameters": { "operation": state } }
              }
        self.send(cmd)
        
    def send(self, cmd):
        cmd = json.dumps(cmd).encode('ascii')
        self.client.sendall(cmd)
        print(cmd)
        data = self.client.recv(1024) #.decode()
        print(data)
        
    def setEtalon(self, value):
        cmd = { "message": {
                "transmission_id": [1001],
                "op": "tune_etalon",
                "parameters": { "setting": [value] } }
              }
        self.send(cmd)
        
    def tuneEtalon(self, f0):
        etalon = 48
        increment = 1
        self.setEtalon(etalon)
        f = self.getFrequency()
        sign = np.sign(f-f0)
        while np.abs(f-f0) > 1:
            oldSign = sign
            etalon += sign*increment
            
            self.setEtalon(etalon)
            f = self.getFrequency()
            
            sign = np.sign(f-f0)
            if sign != oldSign:
                increment *= .1
            
        
    def getFrequency(self):
        return self.wavemeter.frequency()*1000
    
#clientAddr = "192.168.1.120"
server = "192.168.1.207"
port = 39933
client = "192.168.1.1"
m = MSquared(server, port, client)

#m.tuneEtalon(394798.2)

