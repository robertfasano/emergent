from emergent.networks.autoAlign.hubs import AutoAlign
from emergent.networks.autoAlign.things import PicoAmp
from emergent.things import LabJack

def initialize(core, params = {'autoAlign': {'name': '', 'params': {'MEMS':{'params': {'devid': ''}}}}}):
    core.add_params(params)
    devid = params['autoAlign']['params']['MEMS']['params']['devid']
    labjack = LabJack(name='labjack', params = {'devid': devid})
    hub = AutoAlign(name='autoAlign', labjack=labjack, core = core)
    thing = PicoAmp('MEMS', parent=hub, params = {'labjack': labjack, 'type': 'digital'})

    core.add_hub(hub)
