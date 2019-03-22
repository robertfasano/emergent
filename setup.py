from distutils.core import setup
from setuptools import find_packages
import os
import json

setup(
    name='EMERGENT',
    version='0.1dev',
    description='Experimental Machine-learning EnviRonment for Generalized Networked Things',
    author='Robert Fasano',
    author_email='robert.j.fasano@colorado.edu',
    packages=find_packages(exclude=['docs']),
    license='MIT',
    long_description=open('README.md').read(),
    install_requires=['pyqt5==5.9.2', 'pyserial', 'ipython', 'influxdb',
                      'pint', 'matplotlib', 'pandas', 'scipy', 'psutil',
                      'scikit-learn', 'eventlet', 'flask-socketio', 'socketIO_client',
                      'flask', 'jupyter']
)

# packages = ['pyqt5', 'pyqt5-sip', 'pyqt5-tools']
# for pkg in packages:
#     os.system('pip uninstall %s'%pkg)
# os.system('pip install pyqt5==5.9.2')

''' Prepare batch file and shortcut '''
import sys, os
if os.name == 'nt':
    os.system('pip install pywin32')
    scripts_dir = sys.executable.split('python')[0]+'Scripts'

    with open('/emergent_master.cmd', 'w') as file:
        file.write('cd /emergent/emergent\ncall activate emergent\n%s\ipython3.exe -i /emergent/emergent/main.py -- %%1 --addr 127.0.0.1'%scripts_dir)
    with open('/emergent_dashboard.cmd', 'w') as file:
        file.write('cd /emergent/emergent\ncall activate emergent\n%s\ipython3.exe -i /emergent/emergent/dashboard/main.py -- --addr 127.0.0.1'%scripts_dir)
    with open('/emergent_session.cmd', 'w') as file:
        file.write('start "" "/emergent_master.cmd" %1\nstart "" "/emergent_dashboard.cmd"')
elif os.name == 'darwin':
    with open(os.path.expanduser('~/emergent_master.sh'), 'w') as file:
        file.write('source activate emergent\nipython -i ~/emergent/emergent/main.py -- $1')
    with open(os.path.expanduser('~/emergent_dashboard.sh'), 'w') as file:
        file.write('cd ~/emergent/emergent\nsource activate emergent\npython ~/emergent/emergent/dashboard/main.py')
    with open(os.path.expanduser('~/emergent_session.sh'), 'w') as file:
        file.write('open -a Terminal.app ~/emergent_dashboard.sh\n~/emergent_master.sh $1')

with open('config.json', 'w') as file:
    filepath = os.path.realpath(__file__)
    root = os.path.abspath(os.path.join(filepath, '..'))
    json.dump({'path': root+'/emergent'}, file)
