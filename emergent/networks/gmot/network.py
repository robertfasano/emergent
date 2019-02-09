from emergent.networks.gmot.hubs import MOT, Loader
from emergent.things import LabJack, NetControls, Novatech
from emergent.networks.gmot.things import CurrentDriver, IntensityServo
from emergent.networks.autoAlign import network as autoAlign
from emergent.modules.node import Thing

def initialize(network):
    ''' Import autoAlign hubs '''
    cooling_params = {'autoAlign': {'name': 'cooling',
                            'params': {'MEMS':
                                        {'params': {'devid': '470016934'}}}}}
    slowing_params = {'autoAlign': {'name': 'slowing',
                            'params': {'MEMS':
                                        {'params': {'devid': '470017899'}}}}}
    autoAlign.initialize(network, cooling_params)
    autoAlign.initialize(network, slowing_params)


    ''' Define MOT hub '''
    mot = MOT(name='MOT', network = network)
    loading_inputs =  ['probe delay', 'loading time', 'probe time', 'gate time', 'AOM delay']
    loader = Thing(name='loader', parent=mot, params = {'inputs': loading_inputs})
    feedthrough = NetControls('feedthrough', params = {'port': 'COM7'}, parent = mot)
    novatech = Novatech('novatech', params = {'port': 'COM4'}, parent = mot)
    servo = IntensityServo('servo', params = {'devid': '470016973'}, parent = mot)
    coils = CurrentDriver('coils', params = {'devid': '440010680'}, parent = mot)

    ''' Add hubs to network '''
    for hub in [mot]:
        network.addHub(hub)
