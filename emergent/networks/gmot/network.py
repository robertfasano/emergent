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
from emergent.networks.gmot.controls.loader import Loader
from __main__ import *

''' Define autoAlign '''
labjack_cooling = LabJack(devid='470016934', name='cooling')
cooling = AutoAlign(name='cooling', labjack=labjack_cooling, path='networks/%s'%sys.argv[1])
mems_cooling = PicoAmp('MEMS', labjack_cooling, parent=cooling)

labjack_slowing = LabJack(devid='470017899', name='slowing')
slowing = AutoAlign(name='slowing', labjack=labjack_slowing, path='networks/%s'%sys.argv[1])
mems_slowing = PicoAmp('MEMS', labjack_slowing, parent=slowing)

''' Define MOT control hub '''
mot = MOT(name='MOT', path='networks/%s'%sys.argv[1])
loader = Loader(name='loader', parent=mot)
# feedthrough = NetControls('feedthrough', 'COM11', parent = mot)
novatech = Novatech('novatech', 'COM4', parent = mot)
servo = IntensityServo('servo', '470016973', parent = mot)
# agilis = Agilis('COM15', 'agilis', parent=mot)
labjack_coils = LabJack(devid='440010680', name = 'labjack')
coils = CurrentDriver('coils', 'COM13', 'COM18', parent = mot,labjack = labjack_coils)

# devid = '470016973'    # T7
# labjack_MEMS = LabJack(devid=devid)
# mems = PicoAmp('MEMS', labjack_MEMS, parent=mot, comm='analog')
