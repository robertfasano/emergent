from emergent.networks.gmot.hubs import MOT
from emergent.devices import LabJack, NetControls, Novatech
from emergent.networks.gmot.devices import CurrentDriver, IntensityServo
from emergent.networks.autoAlign import network as autoAlign
from emergent.networks.autoAlign4 import network as autoAlign4
from emergent.networks.monitor import network as monitor

def initialize(core, name='gmot', params={}):
    ''' Import autoAlign hubs '''
    autoAlign.initialize(core, params={'devid': '470016934',
                                       'type': 'digital'},
                               name='cooling')
    autoAlign.initialize(core, params={'devid': '470017899',
                                       'type': 'digital'},
                               name='slowing')


    ''' Define MOT hub '''
    mot = MOT(name='MOT', core = core)
    feedthrough = NetControls('feedthrough', params = {'port': 'COM7'}, hub = mot)
    novatech = Novatech('novatech', params = {'port': 'COM4'}, hub = mot)
    servo = IntensityServo('servo', params = {'devid': '470016973'}, hub = mot)
    coils = CurrentDriver('coils', params = {'devid': '440010680'}, hub = mot)

    ''' Import monitor hub '''
    params = {'daqs': [{'name': 'labjack', 'params':{'devid': '470018943'}}],
              'watchdogs': {
                        'Chamber ion pump current': {'threshold': 0.1, 'channel': 'A0', 'units': 'mV'}
                        }
                     }
    monitor.initialize(core, params = params)

    ''' Add hubs to core '''
    for hub in [mot]:
        core.add_hub(hub)
