from emergent.networks.autoAlign4.hubs import AutoAlign
from emergent.networks.autoAlign4.devices import PicoAmp
from emergent.devices import LabJack

''' Cost function will be measured by the FIRST LabJack! '''
def initialize(core, params = {'autoAlign': {'name': '', 'params': {'MEMS':{'params': {'devid': ''}}}}}):


    core.add_params(params)
    hub = None

    for device in params['autoAlign']['params']:
        devid = params['autoAlign']['params'][device]['params']['devid']
        board_type = params['autoAlign']['params'][device]['params']['type']
        labjack = LabJack(name='labjack', params = {'devid': devid})
        if hub is None:
            hub = AutoAlign(name='autoAlign', labjack=labjack, core = core)
        device = PicoAmp(device, hub=hub, params = {'labjack': labjack, 'type': board_type})

    core.add_hub(hub)
