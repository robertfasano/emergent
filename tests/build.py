import os
if os.name == 'nt':
    os.system('./install.cmd')
else:
    os.system('./install.sh')

''' Test documentation '''
os.system('python test_tutorials.py')
