from emergent.networks.autoAlign.hubs import AutoAlign
from emergent.networks.autoAlign.devices import PicoAmp

def initialize(core, params=None, name='autoAlign'):
    assert params is not None
    hub = AutoAlign(name=name, labjack=labjack, core = core)
    device = PicoAmp('MEMS', hub=hub, params = params)

    core.add_hub(hub)
