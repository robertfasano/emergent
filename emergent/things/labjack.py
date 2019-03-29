import numpy as np
from emergent.modules import Thing
import logging as log
from emergent.drivers.labjack import LabJackDriver
from labjack import ljm

class LabJack(Thing, LabJackDriver):
    def __init__(self, name = 'LabJack', parent = None, params = {'device': 'ANY', 'connection': 'ANY', 'devid': 'ANY', 'arange': 10}):
        LabJackDriver.__init__(self, params)
        if parent is not None:
            Thing.__init__(self, name, parent, params = params)
            self.input_channels = ['AIN0', 'AIN1', 'AIN2', 'AIN3']
            if self.deviceType == ljm.constants.dtT4:
                self.digital_channels = ['FIO4', 'FIO5','FIO6','FIO7']
            else:
                self.digital_channels = ['FIO0', 'FIO1', 'FIO2', 'FIO3']
            self.output_channels = ['DAC0', 'DAC1']
            self.channels = {}
            # for channels in [self.input_channels, self.digital_channels, self.output_channels]:
            for channels in [self.output_channels]:
                for ch in channels:
                    self.add_knob(ch)

    def _connect(self):
        if self._connected:
            return
        self._connected = self.connect()

class MultiJack():
    ''' A shared interface for multiple LabJacks. All i/o methods use a composite channel string
        referencing both the LabJack and its channel that you want to access, e.g. 'A0' accesses
        channel 0 of self.labjacks['A']. '''
    def __init__(self, params_list = []):
        self.labjacks = {}
        index = 'A'
        for p in params_list:
            lj = LabJack(name = p['name'], params = p['params'])
            self.labjacks[index] = lj
            index = chr(ord(index)+1)

    def AIn(self, ch):
        return self.labjacks[ch[0]].AIn(int(ch[1::]))

    def AOut(self, ch):
        self.labjacks[ch[0]].AOut(int(ch[1::]))

    def DIn(self, ch):
        return self.labjacks[ch[0]].DIn(int(ch[1::]))

if __name__ == '__main__':
    params = {'device': 'T7', 'connection': 'ETHERNET', 'devid': '470016934', 'arange': 10}
    lj = LabJack(params = params)
