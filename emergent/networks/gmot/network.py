from archetypes.node import Control
from controls.autoAlign import AutoAlign
from controls.mot import MOT
from devices.labjackT7 import LabJack
from devices.picoAmp import PicoAmp
from devices.current_driver import CurrentDriver
from devices.intensity_servo_v2 import IntensityServo
from devices.netcontrols import NetControls
from devices.novatech import Novatech
from __main__ import *

''' Define autoAlign '''
devid = '470016934'
labjack_cooling = LabJack(devid=devid)
cooling = AutoAlign(name='cooling', labjack=labjack_cooling, path='networks/%s'%sys.argv[1])
mems_cooling = PicoAmp('MEMS', labjack_cooling, parent=cooling)

devid = '470016970'
labjack_slowing = LabJack(devid=devid)
slowing = AutoAlign(name='slowing', labjack=labjack_slowing, path='networks/%s'%sys.argv[1])
mems_slowing = PicoAmp('MEMS', labjack_slowing, parent=slowing)

''' Define MOT control hub '''
devid = '440010734'     # T4
labjack_MOT = LabJack(devid=devid)
mot = MOT(name='MOT', labjack=labjack_MOT,path='networks/%s'%sys.argv[1])
coils = CurrentDriver('coils', 'COM13', 'COM18', parent = mot, labjack = labjack_MOT)
feedthrough = NetControls('feedthrough', 'COM11', parent = mot)
novatech = Novatech('novatech', 'COM7', parent = mot)
servo = IntensityServo('servo', None, '440010742', parent = mot)

devid = '470016973'    # T7
labjack_MEMS = LabJack(devid=devid)
mems = PicoAmp('MEMS', labjack_MEMS, parent=mot, comm='analog')

''' Run post-load routine '''
for c in Control.instances:
    c.onLoad()
