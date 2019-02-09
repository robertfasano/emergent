from emergent.modules import Thing
import logging as log
import socket
import time
import json
import numpy as np

class SolsTiS(Thing):
    def __init__(self, params, name = 'SolsTiS', parent = None):
        ''' Args:
                params (dict): dictionary containing the following fields:
                params['server_ip'] (str): IP address of the ICE-BLOC controller
                params['port'] (int): port number
                params['client_ip'] (str): IP address of the PC
        '''

        super().__init__(name=name, parent = parent)
        self.add_input('etalon setpoint')
        self.params = params
        self.options['Toggle lock'] =  self.toggle_lock
        self.options['Acquire lock'] = self.acquire_etalon_lock

    def _connect(self):
        ''' Opens a TCP/IP link to the SolsTiS's ICE-BLOC controller. '''
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.client.connect((self.params['server_ip'], self.params['port']))
        resp = self.message(op = 'start_link', parameters = {'ip_address': self.params['client_ip']})
        print(resp)

        self.lock_state = self.check_etalon_lock()
        self.lock(0)
        return 1

    def _actuate(self, state):
        self.message(op = 'tune_etalon', parameters = {'setting': [state['etalon setpoint']]})

    def acquire_etalon_lock(self):
        ''' if etalon lock is on, remove it '''
        self.lock(0)
        ''' Servo to 0.5 GHz of threshold then cancel and apply lock. Retry if
            lock point is greater than 1 GHz from setpoint. '''

        error = 999
        while np.abs(error) > 1:
            cost_params={'setpoint': 394798.3, 'wait': 0.1}
            algo_params = {'threshold': 'None',
                      'proportional_gain':0.5,
                      'integral_gain':0.05,
                      'derivative_gain':0,
                      'sign':1}
            servo_panel = self.leaf.tree_widget().parent.optimizer.servo_panel
            settings = {'hub': self.parent,
                        'state': {self.name: self.state},
                        'experiment_name': 'error',
                        'algorithm_params': algo_params,
                        'experiment_params': cost_params,
                        'callback': self.callback}
            servo_panel.prepare_optimizer(settings=settings)
            error = self.parent.error(error_params)

    def callback(self, error, threshold=0.5):
        if error is None:
            return True
        if np.abs(error) > threshold:
            return True
        else:
            self.lock(1)
            return False

    def check_etalon_lock(self):
        reply = self.message(op='etalon_lock_status', parameters = {})
        self.lock_state = {'on':1, 'off':0}[reply['message']['parameters']['condition']]
        return self.lock_state

    def toggle_lock(self):
        self.lock(1-self.check_etalon_lock())

    def get_system_status(self):
        reply = self.message(op = 'get_status', parameters = {})
        return reply['message']['parameters']

    def lock(self, state):
        if state == self.lock_state:
            return
        self.lock_state = state
        self.message(op = 'etalon_lock', parameters = {'operation': ['off', 'on'][state]})

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
