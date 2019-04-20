''' This module launches an EMERGENT session.

    Args:
        name: the name of a network in the emergent/networks folder
        --addr: specify an IP address if you want to define localhost for testing
        --port: the networking port of a decentralized EMERGENT session
        --verbose: increase the output verbosity for debugging
'''
#from __main__ import *
import sys
import os
import logging as log
import argparse
from emergent.core import Core

''' Register app with OS '''
if os.name == 'nt':
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('EMERGENT')

''' Parse arguments and set verbosity for logging '''
parser = argparse.ArgumentParser()
parser.add_argument("name", help="Network name")
parser.add_argument("--addr", help='EMERGENT session IP address', default='127.0.0.1')
parser.add_argument("--port", help='EMERGENT session networking port', type=int, default='5000')
parser.add_argument("-v", "--verbose", help="Increase output verbosity", action="store_true")
args = parser.parse_args()
if args.verbose:
    log.basicConfig(level=log.DEBUG)
else:
    log.basicConfig(level=log.INFO)

''' Initialize core  '''
core = Core(name=args.name, addr=args.addr, port=args.port)
core.initialize()        # instantiate nodes
core.load()              # load previous state from file
core.post_load()         # run post-load routine to prepare physical state

from emergent.API.API import serve
serve(core, args.addr, args.port)
print('API running at %s:%i'%(args.addr, args.port))
log.getLogger('werkzeug').setLevel(log.ERROR)
