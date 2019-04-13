from emergent.networks.autoAlign4.hubs import AutoAlign
from emergent.networks.autoAlign4.things import PicoAmp
from emergent.things import LabJack

''' Cost function will be measured by the FIRST LabJack! '''
def initialize(core, params = {'autoAlign': {'name': '', 'params': {'MEMS':{'params': {'devid': ''}}}}}):


    core.add_params(params)
    hub = None

    for thing in params['autoAlign']['params']:
        devid = params['autoAlign']['params'][thing]['params']['devid']
        board_type = params['autoAlign']['params'][thing]['params']['type']
        labjack = LabJack(name='labjack', params = {'devid': devid})
        if hub is None:
            hub = AutoAlign(name='autoAlign', labjack=labjack, core = core)
        thing = PicoAmp(thing, parent=hub, params = {'labjack': labjack, 'type': board_type})

    core.add_hub(hub)
