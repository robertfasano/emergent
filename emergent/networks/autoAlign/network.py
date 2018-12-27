from emergent.networks.autoAlign.hubs import AutoAlign
from emergent.networks.autoAlign.things import PicoAmp
from emergent.things import LabJack

def initialize(network, params = {}):
    network.add_params(params)

    labjack = LabJack(name='labjack', params = {'devid': '470017899'})
    hub = AutoAlign(name='autoAlign', labjack=labjack, network = network)
    thing = PicoAmp('MEMS', labjack, parent=hub)

    network.addHub(hub)
