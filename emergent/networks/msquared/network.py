from emergent.networks.msquared.hubs.lock import Lock
from emergent.networks.msquared.devices import PZT, SolsTiS, Wavemeter
import sys

def initialize(core, params = {}):
    lock = Lock('lattice', core=core, addr='132.163.82.22')
    params = {'server_ip':'192.168.1.207', 'client_ip':'192.168.1.100', 'port':39933}
    s = SolsTiS(params, parent=lock)

    params = {'devid': '440010635'}
    pzt = PZT(params, parent=lock)
    wm = Wavemeter(addr='TCPIP::10.199.199.1::23::SOCKET', parent=lock)
    core.add_hub(lock)
