from emergent.networks.msquared.controls.lock import Lock
from emergent.devices.SolsTiS import SolsTiS
from emergent.devices.bristol import Wavemeter
import sys

lock = Lock('lattice')
params = {'server_ip':'192.168.1.207', 'client_ip':'192.168.1.100', 'port':39933}
s = SolsTiS(params, parent=lock)
wm = Wavemeter(addr='TCPIP::10.199.199.1::23::SOCKET', parent=lock)