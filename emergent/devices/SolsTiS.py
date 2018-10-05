from emergent.archetypes.node import Device
import logging as log
import socket
import time

class SolsTiS(Device):
    def __init__(self, params, name = 'SolsTiS', parent = None):
        super().__init__(name=name, parent = parent)
        self.add_input('etalon setpoint')

    def _connect(self):
        ''' Opens a TCP/IP link to the SolsTiS's ICE-BLOC controller. '''
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.client.connect((self.params['server_ip'], self.params['port']))
        resp = self.message(op = 'start_link', parameters = {'ip_address': self.params['client_ip']})
        print(resp)
        return 1

    def _actuate(self, state):
        self.message(op = 'tune_etalon', parameters = {'setting': [state['etalon setpoint']]})

    def check_etalon_lock(self):
        reply = self.message(op='etalon_lock_status', parameters = {})
        return {'on':1, 'off':0}[reply['message']['parameters']['condition']]

    def get_system_status(self):
        reply = self.message(op = 'get_status', parameters = {})
        return reply['message']['parameters']

    def lock(self, state):
        self.message(op = 'etalon_lock', parameters = {'operation': state})

    def message(self, op, parameters):
        cmd = { "message": {"timestamp":time.time(), "transmission_id": [1001],"op": op,"parameters": parameters }}
        print(cmd)
        self.client.sendall(json.dumps(cmd).encode())
        reply = self.client.recv(1024)
        return json.loads(reply)


if __name__ == '__main__':
    params = {'server_ip':'192.168.1.207', 'client_ip':'192.168.1.1', 'port':39933}