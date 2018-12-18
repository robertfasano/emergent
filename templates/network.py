from emergent.templates.hub import TemplateHub
from emergent.templates.thing import TemplateThing
from __main__ import *

''' Define autoAlign '''
hub = TemplateHub('hub', path='networks/%s'%sys.argv[1])
thing = TemplateThing('thing', parent=hub)
