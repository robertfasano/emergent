from emergent.archetypes.node import Control
from emergent.controls.autoAlign import AutoAlign
from emergent.networks.gmot.controls.mot import MOT
from emergent.devices.labjackT7 import LabJack
from emergent.devices.picoAmp import PicoAmp
from emergent.devices.current_driver import CurrentDriver
from emergent.devices.intensity_servo_v2 import IntensityServo
from emergent.devices.netcontrols import NetControls
from emergent.devices.novatech import Novatech
from emergent.devices.agilis import Agilis
from __main__ import *

''' Define autoAlign '''
devid = '470016934'
labjack_cooling = LabJack(devid=devid, name='cooling')
cooling = AutoAlign(name='cooling', labjack=labjack_cooling, path='networks/%s'%sys.argv[1])
mems_cooling = PicoAmp('MEMS', labjack_cooling, parent=cooling)

devid = '470016970'
labjack_slowing = LabJack(devid=devid, name='slowing')
slowing = AutoAlign(name='slowing', labjack=labjack_slowing, path='networks/%s'%sys.argv[1])
mems_slowing = PicoAmp('MEMS', labjack_slowing, parent=slowing)

''' Define MOT control hub '''
devid = '440010734'     # T4
mot = MOT(name='MOT', path='networks/%s'%sys.argv[1])
labjack_MOT = LabJack(devid=devid, name='labjack', parent=mot)
mot.add_labjack(labjack_MOT)
feedthrough = NetControls('feedthrough', 'COM11', parent = mot)
# novatech = Novatech('novatech', 'COM32', parent = mot)
servo = IntensityServo('servo', None, '440010742', parent = mot)
# agilis = Agilis('COM15', 'agilis', parent=mot)
devid='440010680'
labjack_coils = LabJack(devid=devid, name = 'labjack')
coils = CurrentDriver('coils', 'COM13', 'COM18', parent = mot,labjack = labjack_coils)

# devid = '470016973'    # T7
# labjack_MEMS = LabJack(devid=devid)
# mems = PicoAmp('MEMS', labjack_MEMS, parent=mot, comm='analog')

''' Run post-load routine '''
for c in Control.instances:
    c.onLoad()

''' Run specific processes '''
servo.autolock(2)       # lock slowing beam at 90% max power
