from controls.autoAlign import AutoAlign
from devices.labjackT7 import LabJack
from devices.picoAmp import PicoAmp
from __main__ import *

# devid = '470016934'
# labjack_cooling = LabJack(devid=devid)
# control = AutoAlign(name='control', labjack=labjack_cooling, path='examples/%s'%sys.argv[1])
# mems = PicoAmp('MEMS', labjack_cooling, parent=control)


''' Define autoAlign '''
devid = '470016934'
labjack_cooling = LabJack(devid=devid)
autoAlign_cooling = AutoAlign(name='autoAlign_cooling', labjack=labjack_cooling, path='examples/%s'%sys.argv[1])
mems_cooling = PicoAmp('mems_cooling', labjack_cooling, parent=autoAlign_cooling)

devid = '470016970'
labjack_slowing = LabJack(devid=devid)
autoAlign_slowing = AutoAlign(name='autoAlign_slowing', labjack=labjack_slowing, path='examples/%s'%sys.argv[1])
mems_slowing = PicoAmp('mems_slowing', labjack_slowing, parent=autoAlign_slowing)

''' Define coil drivers '''
devid = '470016973'
port1 = None
port2 = None
labjack_MOT = LabJack(devid=devid)
mot = MOT(name='MOT', labjack=labjack_MOT,path='examples/%s'%sys.argv[1])
coils = CurrentDriver('coils', port1, port2, parent = mot, labjack = labjack_MOT)
