import json
import socket
if os.name == 'posix':        # if using OS X, open a special testing version of the program
    sys.path.append('C:\\Users\\Public\\Documents\\GitHub')
else:
    sys.path.append('/Users/rjf2/Documents/GitHub')
from labAPI.tcpip import TCPIP

def MSquared():
    def __init__(self, addr, port, buffer):
        ''' Open socket connection '''
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((addr, port))
        self.buffer = buffer
        
    def connect(self, clientIP):
        cmd = {
                    "message":
                    {
                            "transmission_id": [999],
                            "op":"start_link",
                            "parameters":
                            {
                                "ip_address": "%s"%clientIP
                            }
                    }
                }
        self.client.send(cmd)

