from emergent.templates.control import TemplateControl
from emergent.templates.device import TemplateDevice
from __main__ import *

''' Define autoAlign '''
control = TemplateControl('control', path='networks/%s'%sys.argv[1])
device = TemplateDevice('device', parent=control)
