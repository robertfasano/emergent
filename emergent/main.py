''' This module launches an EMERGENT session.

    Args:
        name: the name of a network in the emergent/networks folder
        --addr: specify an IP address if you want to define localhost for testing
        --port: the networking port of a decentralized EMERGENT session
        --database_addr: the IP address of a remote InfluxDB server
        --verbose: increase the output verbosity for debugging
'''
#from __main__ import *
import sys
import os
import logging as log
import argparse
import importlib
from emergent.modules.networking import Network
from emergent.utilities.networking import get_address

def launch():
    ''' Register app with OS '''
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('EMERGENT')
    except AttributeError:
        pass
    global network
    char = {'nt': '\\', 'posix': '/'}[os.name]
    sys.path.append(char.join(os.getcwd().split(char)[0:-3]))
    sys.path.append('networks/%s'%sys.argv[1])

    ''' Parse arguments and set verbosity for logging '''
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="Network name")
    parser.add_argument("--addr", help='EMERGENT session IP address')
    parser.add_argument("--port", help='EMERGENT session networking port', type=int)
    parser.add_argument("--database_addr", help='Remote InfluxDB address')

    parser.add_argument("-v", "--verbose", help="Increase output verbosity", action="store_true")
    args = parser.parse_args()
    if args.verbose:
        log.basicConfig(level=log.DEBUG)
    else:
        log.basicConfig(level=log.INFO)

    ''' Initialize network  '''
    if args.addr:
        addr = args.addr
    else:
        addr = '127.0.0.1'
        # addr = get_address()
    port = 5000


    if args.port:
        port = args.port
    database_addr = None
    if args.database_addr:
        database_addr = args.database_addr
    network = Network(name=args.name, addr=addr, port=port, database_addr=database_addr)
    network.initialize()        # instantiate nodes
    network.load()              # load previous state from file
    network.post_load()         # run post-load routine to prepare physical state

    from emergent.API.API import serve
    from threading import Thread
    thread = Thread(target=serve, args = (network, addr, port))
    thread.start()
    log.getLogger('werkzeug').setLevel(log.ERROR)

if __name__ == '__main__':
    launch()
