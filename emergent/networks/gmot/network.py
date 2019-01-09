# from emergent.hubs.autoAlign import AutoAlign
from emergent.networks.gmot.hubs import MOT, Loader
from emergent.things import LabJack, PicoAmp, NetControls, Novatech
from emergent.networks.gmot.things import CurrentDriver, IntensityServo
from emergent.networks.autoAlign import network as autoAlign
from __main__ import *



def initialize(network):
    # ''' Define autoAlign '''
    # labjack_cooling = LabJack(name='cooling', params = {'devid': '470016934'})
    # cooling = AutoAlign(name='cooling', labjack=labjack_cooling)
    # mems_cooling = PicoAmp('MEMS', labjack_cooling, parent=cooling)
    #
    # labjack_slowing = LabJack(name='slowing', params = {'devid': '470017899'})
    # slowing = AutoAlign(name='slowing', labjack=labjack_slowing)
    # mems_slowing = PicoAmp('MEMS', labjack_slowing, parent=slowing)

    ''' Import autoAlign hubs '''
    params = {'autoAlign': {'name': 'cooling',
                            'params': {'MEMS':
                                        {'params': {'devid': '470016934'}}}}}
    params = {'autoAlign': {'name': 'slowing',
                            'params': {'MEMS':
                                        {'params': {'devid': '470017899'}}}}}
    autoAlign.initialize(network, cooling_params)
    autoAlign.initialize(network, slowing_params)


    ''' Define MOT hub '''
    mot = MOT(name='MOT')
    loader = Loader(name='loader', parent=mot)
    feedthrough = NetControls('feedthrough', params = {'port': 'COM11'}, parent = mot)
    novatech = Novatech('novatech', params = {'port': 'COM4'}, parent = mot)
    servo = IntensityServo('servo', params = {'devid': '470016973'}, parent = mot)
    coils = CurrentDriver('coils', params = {'devid': '440010680'}, parent = mot)


    ''' Add hubs to network '''
    for hub in [cooling, slowing, mot]:
        network.addHub(hub)
