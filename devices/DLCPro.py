from toptica.lasersdk.client import Client, SerialConnection
from toptica.lasersdk.dlcpro.v1_6_3 import DLCpro, NetworkConnection


class DLCPro():
    def __init__(self, port='COM14'):
        self.connection = SerialConnection('COM14')         # On Windows
        
    def get_current(self):
        with Client(self.connection) as client:
            print(client.get('laser1:dl:cc:current-act',float))

    def get_current_offset(self):
        with Client(self.connection) as client:
            print(client.get('laser1:scan:offset',float))
            
    def get_emission(self):
        with Client(self.connection) as client:
            print(client.get('laser1:dl:cc:emission',bool))
            
    def toggle_emission(self):
        return

if __name__ == '__main__':
    d = DLCPro(port='COM14')
    d.get_current_offset()


