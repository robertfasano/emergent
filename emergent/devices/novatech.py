import serial
import sys
from emergent.protocols.serial import Serial
from emergent.core import Device, Knob
import logging as log

class Novatech(Device):
    slowing = Knob('slowing')
    trapping = Knob('trapping')

    def __init__(self, name, hub=None, port='COM4'):
        super().__init__(name='novatech', hub = hub)
        self.port=port
    def _connect(self):
        self.serial = self._open_serial(port=self.port)
        return self.serial._connected

    @slowing.command
    def slowing(self, f):
        self.set_frequency(0, f)

    @trapping.command
    def trapping(self, f):
        self.set_frequency(1, f)

    def set_amplitude(self,ch, V):
        self.amplitude[ch] = V
        return self.serial.command('V%i %i'%(ch, V))

    def set_frequency(self,ch, f):
        ''' Args:
                int ch
                str f
                '''
        self.frequency[ch] = f
        return self.serial.command('f%i %s'%(ch, f))

    def write_table(self, channel, sequence, dwell):
        ''' Writes a frequency sequence to the onboard table.

            Args:
                channel (int): 1-4.
                sequence (list): List of frequencies to step through.
                dwell (float): Duration of each step.

            Note:
                The sequence must be uniformly spaced in time.
        '''
        if len(sequence) > 32768:
            log.warn('Could not write sequence to Novatech: too long.')
            return

        self.serial.command('M 0')
        for i in range(len(sequence)):
            cmd = 't%i '%channel        # specify channel

            # specify 2-byte hex RAM address
            addr = format(i, '#04x').split('x')[1]
            cmd += addr + ' '
            # specify 4-byte hex frequency
            freq = hex(struct.unpack('<I', struct.pack('<f', f))[0]).split('x')[1]
            freq = '0'*(8-len(freq)) + freq
            cmd += freq + ','
            # specify 2-byte hex phase offset
            phase = '0000'
            cmd += phase + ','
            # specify 2-byte hex amplitude
            amp = self.amplitude[channel]
            amp = format(amp, '#04x').split('x')[1]
            cmd += amp + ','

            # specify 1-byte hex dwell time in units of 100 us
            dwell = int(dwell / 100e-6)
            t = hex(dwell).split('x')[1]
            if i == len(sequence):
                t = 'ff'        # hold at last frequency
            cmd += t

            self.serial.command(cmd)

    def start_table(self):
        self.serial.command('M t')
