from emergent.networks.gmot.hubs import MOT
from emergent.things import LabJack, NetControls, Novatech
from emergent.networks.gmot.things import CurrentDriver, IntensityServo
from emergent.networks.autoAlign import network as autoAlign
from emergent.networks.autoAlign4 import network as autoAlign4
from emergent.core.node import Thing
from emergent.networks.monitor import network as monitor

def initialize(core):
    ''' Import autoAlign hubs '''
    cooling_params = {'autoAlign': {'name': 'cooling',
                            'params': {'MEMS':
                                        {'params': {'devid': '470016934'}}}}}
    slowing_params = {'autoAlign': {'name': 'slowing',
                            'params': {'MEMS':
                                        {'params': {'devid': '470017899'}}}}}
    slowing_params = {'autoAlign': {'name': 'slowing',
                            'params': {'MEMS': {'params': {'devid': '470017899', 'type': 'digital'}},
                                       'MEMS2': {'params': {'devid': '470018943', 'type': 'analog'}}

                                        }}}

    autoAlign.initialize(core, cooling_params)
    autoAlign4.initialize(core, slowing_params)


    ''' Define MOT hub '''
    mot = MOT(name='MOT', core = core)
    feedthrough = NetControls('feedthrough', params = {'port': 'COM7'}, parent = mot)
    novatech = Novatech('novatech', params = {'port': 'COM4'}, parent = mot)
    servo = IntensityServo('servo', params = {'devid': '470016973'}, parent = mot)
    coils = CurrentDriver('coils', params = {'devid': '440010680'}, parent = mot)

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
