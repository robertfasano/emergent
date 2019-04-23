from emergent.networks.autoAlign.hubs import AutoAlign
from emergent.networks.autoAlign.devices import PicoAmp
from emergent.devices import LabJack

def initialize(core, params=None, name='autoAlign'):
    assert params is not None
    labjack = LabJack(name='labjack', params = {'devid': params['devid']})

    hub = AutoAlign(name=name, labjack=labjack, core = core)
    device = PicoAmp('MEMS', hub=hub, params = {'labjack': labjack, 'type': 'digital'})

    core.add_hub(hub)
