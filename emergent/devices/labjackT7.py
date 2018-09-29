from labjack import ljm
from random import randrange
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import scipy.signal as sig
from scipy.stats import linregress
import time
from threading import Thread
from emergent.archetypes.parallel import ProcessHandler
from emergent.archetypes.fifo import FIFO
from emergent.archetypes.node import Device
import logging as log
import decorator

@decorator.decorator
def queue(func, *args, **kwargs):
    obj = args[0]
    id = time.time()
    q = getattr(obj, 'queue')
    q.add(func, id, *args, **kwargs)
    while True:
        try:
            return q.buffer[id]
        except KeyError:
            continue

class LabJack(ProcessHandler, Device):
    ''' Python interface for the LabJack T7. '''

    def __init__(self, device = "ANY", connection = "ANY", devid = "ANY", arange = 10, name = 'LabJack', parent = None):
        ''' Attempt to connect to a LabJack.

            Args:
                device (str): Device type ("ANY", "T7" are currently supported).
                connection (str): Desired connection type ("ANY", "USB", "TCP", "ETHERNET", or "WIFI").
                devid (str): Serial number, which can be found on the underside of the LabJack.
                arange (float): analog input range.'''
        ProcessHandler.__init__(self)
        self.parent = parent
        if parent is not None:
            Device.__init__(self, name, parent)
        self.device = device
        self.connection = connection
        self.devid = devid
        self.arange = arange
        self.name = name
        self._connected = 0
        self.averaging_array = []

        ''' Define a FIFO queue running in a separate thread so that multiple
            simultaneous threads can share a LabJack without interference. '''
        self.queue = FIFO()
        self._run_thread(self.queue.run)
        self._connected = self._connect()

    def _connect(self):
        if self._connected:
            return
        try:
            self.handle = ljm.openS(self.device, self.connection, self.devid)
            info = ljm.getHandleInfo(self.handle)

            self.deviceType = info[0]
            assert self.deviceType in [ljm.constants.dtT7, ljm.constants.dtT4]
            if self.deviceType == ljm.constants.dtT7:
                self._command('AIN_ALL_RANGE', self.arange)
            log.info('Connected to LabJack (%i).'%(info[2]))
            self.clock = 80e6       # internal clock frequency

            if self.parent is not None:
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
                        self.add_input(ch)

            return 1

        except Exception as e:
            log.error('Failed to connect to LabJack (%s): %s.'%(self.devid, e))

    def _actuate(self, state):
        for key in state:
            prefix = key[0:3]
            channel = int(key[3])
            value = float(state[key])
            if prefix == 'DAC':
                self.AOut(channel, value)
                self.channels[key] = value
            elif prefix == 'FIO':
                self.DOut(channel, value)
                self.channels[key] = value
            elif prefix == 'AIN':
                self.channels[key] = self.AIn(channel)

    @queue
    def _command(self, register, value):
        ''' Writes a value to a specified register.

            Args:
                register (str): a Modbus register on the LabJack.
                value: the value to write to the register.
                '''
        ljm.eWriteName(self.handle, register, value)

    ''' Analog I/O '''
    @queue
    def AIn(self, channel, num = 1):
        ''' Read a channel with optional averaging.

            Args:
                channel (int): number of the target AIN channel.
                num (int): number of measurements to perform and average.
        '''
        vals = []
        for i in range(num):
            vals.append(ljm.eReadName(self.handle, 'AIN%i'%channel))
        return np.mean(vals)

    def AOut(self, channel, value, HV=False):
        ''' Output an analog voltage.

            Args:
                channel (int): number of the target DAC channel.
                value (float): Voltage in volts.
                HV (bool): If False, use a DAC channel (0-5 V); if True, use a TDAC channel with the LJTick-DAC accessory (+/-10 V).
        '''
        if not HV:
            self._command('%s%i'%('DAC', channel), value)
        else:
            self._command("TDAC%i"%channel, value)

    ''' Digital I/O '''
    def DOut(self, channel, state):
        ''' Output a digital signal.

            Args:
                channel (str): a digital channel on the LabJack, e.g. 'FIO4'.
                state (int): 1 or 0
        '''
        if type(channel) is int:
            channel = 'FIO%i'%channel
        self._command(channel, state)

    def PWM(self, channel, frequency, duty_cycle):
        ''' Starts pulse width modulation on an FIO channel.

            Args:
                channel (int): FIO channel to use (0 or 2-5).
                frequency (float): desired frequency in Hz
                duty_cycle (float): duty cycle between 0 and 100.
        '''
        try:
            roll_value = self.clock / frequency
            config_a = duty_cycle * roll_value / 100
            self._command("DIO_EF_CLOCK0_ENABLE", 0);    # Disable the clock source
            self._command("DIO_EF_CLOCK0_DIVISOR", 1); 	# Configure Clock0's divisor
            self._command("DIO_EF_CLOCK0_ROLL_VALUE", roll_value); 	# Configure Clock0's roll value
            self._command("DIO_EF_CLOCK0_ENABLE", 1); 	# Enable the clock source

            # Configure EF Channel Registers:
            self._command("DIO%i_EF_ENABLE"%channel, 0); 	# Disable the EF system for initial configuration
            self._command("DIO%i_EF_INDEX"%channel, 0); 	# Configure EF system for PWM
            self._command("DIO%i_EF_OPTIONS"%channel, 0); 	# Configure what clock source to use: Clock0
            self._command("DIO%i_EF_CONFIG_A"%channel, config_a); 	# Configure duty cycle
            self._command("DIO%i_EF_ENABLE"%channel, 1); 	# Enable the EF system, PWM wave is now being outputted
        except Exception as e:
            log.warn(e)

    def PWM_stop(self, channel):
        self._command("DIO%i_EF_ENABLE"%channel, 0)

    ''' SPI methods '''
    def spi_initialize(self, mode = 3, CLK=0, CS=1,MOSI=2, MISO=3):  #, CS, CLK, MISO, MOSI):
        ''' Initializes the SPI bus using several FIO ports.

            Args:
                CS (int): the FIO channel to use as chip select
                CLK (int): the FIO channel to use as the clock
                MISO (int): the FIO channel to use for input
                MOSI (int): the FIO channel to use for output
        '''

        self._command("SPI_CS_DIONUM", CS)
        self._command("SPI_CLK_DIONUM", CLK)
        self._command("SPI_MISO_DIONUM", MISO)
        self._command("SPI_MOSI_DIONUM", MOSI)
        self._command("SPI_MODE", mode)                  # Selecting Mode CPHA=1 (bit 0), CPOL=1 (bit 1)
        self._command("SPI_SPEED_THROTTLE", 0)        # Valid speed throttle values are 1 to 65536 where 0 = 65536 ~ 800 kHz
        self._command("SPI_OPTIONS", 0)               # Enabling active low clock select pin

    def spi_write(self, data):
        ''' Writes a list of commands via SPI.

            Args:
                data (list): a list of bytes to send through MOSI.
        '''
        numBytes = len(data)
        self._command("SPI_NUM_BYTES", numBytes)

        # Write the bytes
        ljm.eWriteNameByteArray(self.handle, "SPI_DATA_TX", len(data), data)
        self._command("SPI_GO", 1)  # Do the SPI communications

    ''' Streaming methods '''
    def prepare_streamburst(self, channel, trigger = None):
        ''' Sets up the LabJack for burst input streaming on a target channel. '''
        self.aScanList = ljm.namesToAddresses(1, ['AIN%i'%channel])[0]  # Scan list addresses for streamBurst
        if trigger is None:
            self._command("STREAM_TRIGGER_INDEX", 0) # disable triggered stream
        else:
            channel = 'DIO%i'%trigger
            aNames = ["%s_EF_ENABLE"%channel, "%s_EF_INDEX"%channel,
                      "%s_EF_OPTIONS"%channel, "%s_EF_VALUE_A"%channel,
                      "%s_EF_ENABLE"%channel]
            aValues = [0, 3, 0, 2, 1]
            ljm.eWriteNames(self.handle, len(aNames), aNames, aValues)
            self._command('STREAM_TRIGGER_INDEX', 2000+trigger)
            ljm.writeLibraryConfigS('LJM_STREAM_RECEIVE_TIMEOUT_MS',0)  #disable timeout
        if self.deviceType == ljm.constants.dtT7:
            self._command("STREAM_CLOCK_SOURCE", 0)  # enable internal clock
        aNames = ["AIN_ALL_NEGATIVE_CH", "AIN0_RANGE", "AIN1_RANGE",
                  "STREAM_SETTLING_US", "STREAM_RESOLUTION_INDEX"]
        aValues = [ljm.constants.GND, 10.0, 10.0, 0, 0]
        numFrames = len(aNames)
        ljm.eWriteNames(self.handle, numFrames, aNames, aValues)

        self._command('STREAM_BUFFER_SIZE_BYTES', 2**14)

    def streamburst(self, duration, operation = None):
        ''' Performs a burst stream and optionally performs a numpy array operation
            on the result.

            Args:
                duration (float): number of seconds to stream. Scan rate will be
                automatically adjusted to avoid overfilling the buffer.

                '''
        max_samples = 2**13-1
        if self.deviceType == ljm.constants.dtT7:
            max_speed = 100000
        elif self.deviceType == ljm.constants.dtT4:
            max_speed = 40000
        scanRate = np.min([max_samples / duration, max_speed])
        scanRate, aData = ljm.streamBurst(self.handle, 1, self.aScanList, scanRate, max_samples)

        if operation is None:
            return aData
        else:
            return getattr(np, operation)(aData)

    @queue
    def stream_stop(self):
        ljm.eStreamStop(self.handle)

    def stream_out(self, channels, data, scanRate, loop = False, trigger = None):
        ''' Streams data at a given scan rate..

            Args:
                channels (list)): DAC channels to use; can use DAC0, DAC1, or both.
                data (array): Data to stream out.
                loop (bool): if False, data will be streamed out once; if True, the stream will loop.

            Note:
                The maximum buffer size of the LabJack T7 is 2^15=32768 bytes,
                so up to 2^14=16384 samples can be held. At the default stream
                rate of 100 kS/s, this corresponds to 163.84 ms of data. If we
                want to stream for longer than that, we need to repeatedly write
                half a buffer's worth of data each time the buffer is half full.
        '''
        try:
            ''' Stop streaming if currently running '''
            ljm.eStreamStop(self.handle)
        except:
            pass
        buffer_size = 2**14
        if trigger is None:
            self._command("STREAM_TRIGGER_INDEX", 0)        # Ensure triggered stream is disabled.
        else:

            channel = 'DIO%i'%trigger
            aNames = ["%s_EF_ENABLE"%channel, "%s_EF_INDEX"%channel,
                      "%s_EF_OPTIONS"%channel, "%s_EF_VALUE_A"%channel,
                      "%s_EF_ENABLE"%channel]
            aValues = [0, 3, 0, 2, 1]
            ljm.eWriteNames(self.handle, len(aNames), aNames, aValues)
            self._command('STREAM_TRIGGER_INDEX', 2000+trigger)

        if self.deviceType == ljm.constants.dtT7:
            self._command("STREAM_CLOCK_SOURCE", 0)       # Enabling internally-clocked stream.
        aNames = ["STREAM_SETTLING_US", "STREAM_RESOLUTION_INDEX"]
        aValues = [0, 0]
        ljm.eWriteNames(self.handle, len(aNames), aNames, aValues)
        aScanList = []
        if len(channels) > 1:
            for i in range(len(channels)):
                self._command("STREAM_OUT%i_TARGET"%i, 1000+i*2)
                self._command("STREAM_OUT%i_BUFFER_SIZE"%i, buffer_size)
                self._command("STREAM_OUT%i_ENABLE"%i, 1)
                target = ['STREAM_OUT%i_BUFFER_F32'%i] * len(data[:,i])
                ljm.eWriteNames(self.handle, len(data[:,i]), target, list(data[:,i]))
                self._command("STREAM_OUT%i_LOOP_SIZE"%i, len(data[:,i]))
                self._command("STREAM_OUT%i_SET_LOOP"%i, loop)
                aScanList.append(4800+i)
        else:
            i = channels[0]
            self._command("STREAM_OUT0_TARGET", 1000+i*2)
            self._command("STREAM_OUT0_BUFFER_SIZE", buffer_size)
            self._command("STREAM_OUT0_ENABLE", 1)
            target = ['STREAM_OUT0_BUFFER_F32'] * len(data)
            ljm.eWriteNames(self.handle, len(data), target, list(data))
            self._command("STREAM_OUT0_LOOP_SIZE", len(data))
            self._command("STREAM_OUT0_SET_LOOP", loop)
            aScanList.append(4800)
        scanRate = ljm.eStreamStart(self.handle, 1,len(aScanList), aScanList, scanRate)
        log.info("\nStream started with a scan rate of %0.0f Hz." % scanRate)

    def sequence2stream(self, sequence, period, channels = 1):
        ''' Converts a sequence to a stream. The LabJack has two limitations:
            a maximum stream rate of 100 kS/s and a maximum sample count of
            2^13-1. This method computes a cutoff period based on these two
            restrictions; above the cutoff, the speed will be lowered to accommodate
            longer sequences with equal numbers of samples, while below the cutoff,
            the number of samples will be lowered while the speed is kept at max.

            Args:
                sequence (list): A list of tuples describing all changes in a setpoint; e.g. [(0,0), (0.5,1)] describes a setpoint which is switched from 0 to 1 at t=0.5.
                period (float): The total sequence duration.
                channels (int): Number of channels which will be simultaneously streamed; the maximum sampling rate is reduced by this factor.

            Returns:
                stream (array): A list of points which will be output at the calculated sampling rate.
                speed (float): Stream rate in samples/second.
        '''
        buffer_size = 2**14
        max_samples = int(buffer_size/2)-1
        if self.deviceType == ljm.constants.dtT7:
            max_speed = 100000 / channels
        elif self.deviceType == ljm.constants.dtT4:
            max_speed = 40000 / channels

        cutoff = max_samples / max_speed
        if period >= cutoff:
            samples = max_samples
            speed = samples/period
        else:
            speed = max_speed
            samples = period*speed

        stream = np.zeros(int(samples))

        for point in sequence:
            t = point[0]
            V = point[1]
            stream[int(t/period*samples)::] = V
        return stream, speed

    def resample(self, wave, period, channels = 1):
        ''' Resamples a waveform with a given period into the optimal stream.

            Args:
                wave (array): An array of values describing a waveform.
                period (float): The total sequence duration.
                channels (int): Number of channels which will be simultaneously streamed; the maximum sampling rate is reduced by this factor.

            Returns:
                stream (array): A list of points which will be output at the calculated sampling rate.
                speed (float): Stream rate in samples/second.
        '''
        seq = []
        for i in range(len(wave)):
            t = i*period/len(wave)
            x = wave[i]
            seq.append((t, x))

        return self.sequence2stream(seq, period, channels)

if __name__ == '__main__':
    lj = LabJack(devid='470016973')
    sequence = [(0,0), (0.05,1)]
    period = .1
    stream, speed = lj.sequence2stream(sequence, period)
    lj.stream_out([0], stream, speed, trigger = 0)
    for i in range(100):
        lj.DOut(2,i%2)
