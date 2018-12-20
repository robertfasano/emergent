from distutils.core import setup
from setuptools import find_packages
setup(
    name='EMERGENT',
    version='0.1dev',
    description='Experimental Machine-learning EnviRonment for Generalized Networked Things',
    author='Robert Fasano',
    author_email='robert.j.fasano@colorado.edu',
    packages=find_packages(exclude=['docs']),
    license='MIT',
    long_description=open('README.md').read(),
)

''' Prepare batch file and shortcut '''
import sys
scripts_dir = sys.executable.split('python')[0]+'Scripts/'
with open('emergent/run.cmd', 'w') as file:
    file.write('@ECHO OFF\ncall %sactivate.bat\ncall python launcher.py'%scripts_dir)

import win32com.client
import os
ws = win32com.client.Dispatch("wscript.shell")
shortcut = ws.CreateShortcut('emergent/EMERGENT.lnk')
shortcut.TargetPath = 'C:/Windows/System32/cmd.exe'
shortcut.Arguments = '/k "%s/emergent/run.cmd"'%os.getcwd()
shortcut.IconLocation = '%s/emergent/gui/media/icon.ico'%os.getcwd()

shortcut.Save()
