import serial
import sys
from emergent.protocols.serial import Serial
from emergent.modules import Thing
import logging as log

class E4430B(Thing):
    def __init__(self, name, params = {}, parent = None):
        super().__init__(name=name, params = params, parent = parent)
        self._connected = self._connect()
        self.add_knob('frequency')
        self.add_knob('amplitude')

    def _connect(self):
        import visa
        rm = visa.ResourceManager()
        self.client = rm.open_resource('GPIB0::29::INSTR')
        return 1

    def _actuate(self, state):
        ''' set frequency '''
        if 'frequency' in state:
            self.client.write('FREQuency %f MHz'%state['frequency'])

        ''' set amplitude '''
        if 'amplitude' in state:
            self.client.write('POWer %f dBm'%state['amplitude'])
