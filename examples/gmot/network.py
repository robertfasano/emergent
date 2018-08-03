from controls.autoAlign import AutoAlign
from devices.labjackT7 import LabJack
from devices.picoAmp import PicoAmp
from __main__ import *

devid = '470016934'
labjack = LabJack(devid=devid)
control = AutoAlign(name='control', labjack=labjack, path='examples/%s'%sys.argv[1])
mems = PicoAmp('MEMS', labjack, parent=control)
