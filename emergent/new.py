''' A script which creates a new network with the required directories. '''
import sys
import pathlib
base_path = 'networks/%s/'%sys.argv[1]

''' Make network directory '''
pathlib.Path(base_path).mkdir(parents=True, exist_ok=True)

''' Make subdirectories '''
for dir in ['data', 'hubs', 'params', 'state', 'things', 'watchdogs']:
    pathlib.Path(base_path+dir).mkdir(parents=True, exist_ok=True)
    ''' Add init.py file to each subdirectory '''

''' Clone template network.py file '''
