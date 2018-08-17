from emergent.archetypes.node import Control
from emergent.controls.autoAlign import AutoAlign
from emergent.controls.mot import MOT
from emergent.devices.labjackT7 import LabJack
from emergent.devices.picoAmp import PicoAmp
from emergent.devices.current_driver import CurrentDriver
from emergent.devices.intensity_servo_v2 import IntensityServo
from emergent.devices.netcontrols import NetControls
from emergent.devices.novatech import Novatech
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
feedthrough = NetControls('feedthrough', 'COM11', parent = mot)
novatech = Novatech('novatech', 'COM7', parent = mot)
servo = IntensityServo('servo', None, '440010742', parent = mot)

devid='440010680'
labjack_coils = LabJack(devid=devid)
coils = CurrentDriver('coils', 'COM33', 'COM38', parent = mot, labjack = labjack_coils)


# devid = '470016973'    # T7
# labjack_MEMS = LabJack(devid=devid)
# mems = PicoAmp('MEMS', labjack_MEMS, parent=mot, comm='analog')

''' Run post-load routine '''
for c in Control.instances:
    c.onLoad()
