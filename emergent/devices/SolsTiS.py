from emergent.core import Device, Knob
import socket
import time
import json
import numpy as np

class SolsTiS(Device):
    etalon = Knob('etalon')
    etalon_lock = Knob('etalon lock')

    def __init__(self, params, name = 'SolsTiS', hub = None):
        ''' Args:
                params (dict): dictionary containing the following fields:
                params['server_ip'] (str): IP address of the ICE-BLOC controller
                params['port'] (int): port number
                params['client_ip'] (str): IP address of the PC
        '''

        super().__init__(name=name, hub = hub)
        self.params = params

    def _connect(self):
        ''' Opens a TCP/IP link to the SolsTiS's ICE-BLOC controller. '''
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.client.connect((self.params['server_ip'], self.params['port']))
        resp = self.message(op = 'start_link', parameters = {'ip_address': self.params['client_ip']})
        print(resp)

        self.lock_state = self.check_etalon_lock()
        self.lock(0)
        return 1

    @etalon.command
    def etalon(self, V):
        self.message(op = 'tune_etalon', parameters = {'setting': [V]})

    @etalon_lock.query
    def etalon_lock(self):
        reply = self.message(op='etalon_lock_status', parameters = {})
        return {'on':1, 'off':0}[reply['message']['parameters']['condition']]

    @etalon_lock.command
    def etalon_lock(self, state):
        assert state in [0, 1]
        self.message(op = 'etalon_lock', parameters = {'operation': ['off', 'on'][state]})

    def get_system_status(self):
        reply = self.message(op = 'get_status', parameters = {})
        return reply['message']['parameters']

    def message(self, op, parameters):
        ''' Note: ICE-BLOC protocol manual specifies that all numerical parameters should be enclosed in quotes or brackets;
            this does not appear to be strictly necessary, but may prevent transmission errors. '''
        cmd = { "message": {"timestamp":time.time(), "transmission_id": [1001],"op": op,"parameters": parameters }}
        print(cmd)
        self.client.sendall(json.dumps(cmd).encode())
        reply = self.client.recv(1024)
        return json.loads(reply)


if __name__ == '__main__':
    params = {'server_ip':'192.168.1.207', 'client_ip':'192.168.1.100', 'port':39933}
    s = SolsTiS(params)
