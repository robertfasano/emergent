''' A script which creates a new network with the required directories. '''
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("name", help="Network name")
parser.add_argument("-templates", "-t", action='append', help='Template to import')
args, unknown = parser.parse_known_args()
import sys
import pathlib
base_path = 'networks/%s/'%args.name

''' Make network directory '''
pathlib.Path(base_path).mkdir(parents=True, exist_ok=True)

''' Make subdirectories '''
for dir in ['data', 'hubs', 'params', 'state', 'things', 'watchdogs']:
    pathlib.Path(base_path+dir).mkdir(parents=True, exist_ok=True)
    ''' Add init.py file to each subdirectory '''

''' Import the target network '''
templates = args.templates
lines = []

lines.append('\n\n')
lines.append('def initialize(network, params = {}):')
lines.append('\n\t network.add_params(params)')
lines.append('\n')
if templates is not None:
    for template in templates:
        lines.append('\n\t from emergent.networks.%s import network as nw'%template)
    for template in templates:
        lines.append('\n\t nw_params = {}')
        lines.append('\n\t nw.initialize(network, nw_params)')
with open(base_path+'network.py', 'w') as file:
    file.writelines(lines)
