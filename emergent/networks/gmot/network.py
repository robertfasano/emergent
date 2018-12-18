from emergent.hubs.autoAlign import AutoAlign
from emergent.networks.gmot.hubs import MOT, Loader
from emergent.things import LabJack, PicoAmp, NetHubs, Novatech
from emergent.networks.gmot.things import CurrentDriver, IntensityServo
from __main__ import *



def initialize(network):
    ''' Define autoAlign '''
    labjack_cooling = LabJack(devid='470016934', name='cooling')
    cooling = AutoAlign(name='cooling', labjack=labjack_cooling, path='networks/%s'%sys.argv[1])
    mems_cooling = PicoAmp('MEMS', labjack_cooling, parent=cooling)
    network.addHub(cooling)

    labjack_slowing = LabJack(devid='470017899', name='slowing')
    slowing = AutoAlign(name='slowing', labjack=labjack_slowing, path='networks/%s'%sys.argv[1])
    mems_slowing = PicoAmp('MEMS', labjack_slowing, parent=slowing)
    network.addHub(slowing)

    ''' Define MOT hub '''
    mot = MOT(name='MOT', path='networks/%s'%sys.argv[1])
    loader = Loader(name='loader', parent=mot)
    # feedthrough = NetHubs('feedthrough', 'COM11', parent = mot)
    novatech = Novatech('novatech', 'COM4', parent = mot)
    servo = IntensityServo('servo', '470016973', parent = mot)
    labjack_coils = LabJack(devid='440010680', name = 'labjack')
    coils = CurrentDriver('coils', 'COM13', 'COM18', parent = mot,labjack = labjack_coils)
    network.addHub(mot)
