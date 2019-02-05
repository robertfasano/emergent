from emergent.networks.autoAlign.hubs import AutoAlign
from emergent.networks.autoAlign.things import PicoAmp
from emergent.things import LabJack

def initialize(network, params = {'autoAlign': {'name': '', 'params': {'MEMS':{'params': {'devid': ''}}}}}):
    network.add_params(params)
    devid = params['autoAlign']['params']['MEMS']['params']['devid']
    labjack = LabJack(name='labjack', params = {'devid': devid})
    hub = AutoAlign(name='autoAlign', labjack=labjack, network = network)
    thing = PicoAmp('MEMS', parent=hub, params = {'labjack': labjack, 'type': 'digital'})

    network.addHub(hub)
