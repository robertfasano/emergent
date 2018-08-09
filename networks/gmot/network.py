from archetypes.node import Control
from controls.autoAlign import AutoAlign
from controls.mot import MOT
from devices.labjackT7 import LabJack
from devices.picoAmp import PicoAmp
from devices.current_driver import CurrentDriver
from devices.intensity_servo import IntensityServo
from devices.netcontrols import NetControls
from __main__ import *

''' Define autoAlign '''
devid = '470016934'
labjack_cooling = LabJack(devid=devid)
autoAlign_cooling = AutoAlign(name='autoAlign_cooling', labjack=labjack_cooling, path='networks/%s'%sys.argv[1])
mems_cooling = PicoAmp('mems_cooling', labjack_cooling, parent=autoAlign_cooling)
servo_cooling = IntensityServo('servo_cooling', labjack_cooling, 1, 0, parent = autoAlign_cooling)

devid = '470016970'
labjack_slowing = LabJack(devid=devid)
autoAlign_slowing = AutoAlign(name='autoAlign_slowing', labjack=labjack_slowing, path='networks/%s'%sys.argv[1])
mems_slowing = PicoAmp('mems_slowing', labjack_slowing, parent=autoAlign_slowing)
servo_slowing = IntensityServo('servo_slowing', labjack_slowing, 1, 0, parent = autoAlign_slowing)


''' Define MOT control hub '''
devid = '470016973'
port1 = None
port2 = None
labjack_MOT = LabJack(devid=devid)
mot = MOT(name='MOT', labjack=labjack_MOT,path='networks/%s'%sys.argv[1])
coils = CurrentDriver('coils', 'COM13', 'COM18', parent = mot, labjack = labjack_MOT)
feedthrough = NetControls('feedthrough', 'COM11', parent = mot)

''' Run post-load routine '''
for c in Control.instances:
    c.onLoad()
