import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-1]))
from emergent.archetypes.node import Control
from emergent.devices.picoAmp import PicoAmp
from emergent.devices.labjackT7 import LabJack
from emergent.controls.autoAlign import AutoAlign
import numpy as np

class AutoAlign(Control):
        def __init__(name, labjack, parent=None):
                super().__init__(name, parent)
                self.labjack = LabJack()
                
        def cost(state):
                self.actuate(state)
                return self.labjack.AIn(0)

devid = '160049734'
labjack = LabJack(devid=devid)
control = AutoAlign(name='control', labjack=labjack)

mems = PicoAmp('MEMS', labjack, parent=control)
mems.add_input('X', 0, 0, 1)
mems.add_input('Y', 0, 0, 1)

