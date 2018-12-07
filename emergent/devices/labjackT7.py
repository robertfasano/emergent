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
        self.stream_mode = None

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

    @queue
    def _write_array(self, registers, values):
        ljm.eWriteNames(self.handle, len(registers), registers, values)

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

    def DIO_STATE(self, channels, states):
        # prepare inhibit array
        inhibit = ''
        for i in range(23):
            if 23-i-1 in channels:
                inhibit += '0'
            else:
                inhibit += '1'
        inhibit = int(inhibit, 2)
        self._command('DIO_INHIBIT', inhibit)

        # set direction
        bitmask = 0
        for ch in channels:
            bitmask = bitmask | 1 << ch
        self._command('DIO_DIRECTION', bitmask)

        # prepare state array
        bitmask = 0
        for i in range(len(channels)):
            bitmask = bitmask | (states[i] << channels[i])
        self._command('DIO_STATE', bitmask)


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
            aNames = [
                "DIO_EF_CLOCK0_ENABLE", # Disable the clock source
                "DIO_EF_CLOCK0_DIVISOR",    # Configure Clock0's divisor
                "DIO_EF_CLOCK0_ROLL_VALUE", # Configure Clock0's roll value
                "DIO_EF_CLOCK0_ENABLE", # Enable the clock source
                "DIO%i_EF_ENABLE"%channel, 	# Disable the EF system for initial configuration
                "DIO%i_EF_INDEX"%channel, 	# Configure EF system for PWM
                "DIO%i_EF_OPTIONS"%channel,	# Configure what clock source to use: Clock0
                "DIO%i_EF_CONFIG_A"%channel,	# Configure duty cycle
                "DIO%i_EF_ENABLE"%channel    # Enable the EF system, PWM wave is now being outputted
            ]
            aValues = [0,1,roll_value,1,0,0,0,config_a,1]
            self._write_array(aNames, aValues)
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
        aNames = [
            "SPI_CS_DIONUM",
            "SPI_CLK_DIONUM",
            "SPI_MISO_DIONUM",
            "SPI_MOSI_DIONUM",
            "SPI_MODE",                 # Selecting Mode CPHA=1 (bit 0), CPOL=1 (bit 1)
            "SPI_SPEED_THROTTLE",     # Valid speed throttle values are 1 to 65536 where 0 = 65536 ~ 800 kHz
            "SPI_OPTIONS"              # Enabling active low clock select pin
        ]

        aValues = [CS, CLK, MISO, MOSI, mode, 0, 0]
        self._write_array(aNames, aValues)

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
    def prepare_digital_stream(self, channels):
        # prepare inhibit array
        inhibit = ''
        for i in range(23):
            if 23-i-1 in channels:
                inhibit += '0'
            else:
                inhibit += '1'
        inhibit = int(inhibit, 2)
        self._command('DIO_INHIBIT', inhibit)

        # set direction
        bitmask = 0
        for ch in channels:
            bitmask = bitmask | 1 << ch
        self._command('DIO_DIRECTION', bitmask)

    def state_bitmask(self, channels, states):
        bitmask = 0
        for i in range(len(channels)):
            bitmask = bitmask | (states[i] << channels[i])
        return bitmask

    def digital_stream(self, channels = [1,3], period = 1e-3):
        self.prepare_digital_stream(channels)
        t = np.linspace(0,1,100)
        Y = np.zeros((len(t),2))

        Y[t<0.5, 0] = 1
        Y[t<0.7, 1] = 1

        ''' convert multidimensional array to array of bitmasks '''
        y = self.array_to_bitmask(Y, channels)

        self.prepare_stream_out()
        y, f = self.resample(np.atleast_2d(y).T, period)

        self.stream_out(['FIO_STATE'], y.astype(int), f, loop = 1)

    def array_to_bitmask(self, arr, channels):
        ''' Convert multidimensional array with one column for each channel to an array of bitmasks. '''
        y = np.zeros(len(arr))
        for i in range(len(arr)):
            states = arr[i,:]
            bitmask = 0
            for j in range(len(channels)):
                bitmask = bitmask | (int(states[j]) << channels[j])
            y[i] = bitmask
        return y

    def prepare_streamburst(self, channel, max_samples = 2**13-1, trigger = None):
        ''' Sets up the LabJack for burst input streaming on a target channel. '''
        self.aScanList = ljm.namesToAddresses(1, ['AIN%i'%channel])[0]  # Scan list addresses for streamBurst

        if trigger is None:
            self._command("STREAM_TRIGGER_INDEX", 0) # disable triggered stream
            aNames = ['STREAM_TRIGGER_INDEX']
            aValues = [0]
        else:
            channel = 'DIO%i'%trigger
            aNames = ["%s_EF_ENABLE"%channel, "%s_EF_INDEX"%channel,
                      "%s_EF_OPTIONS"%channel, "%s_EF_VALUE_A"%channel,
                      "%s_EF_ENABLE"%channel, 'STREAM_TRIGGER_INDEX']
            aValues = [0, 3, 0, 2, 1, 2000+trigger]
            # self._command('STREAM_TRIGGER_INDEX', 2000+trigger)
            ljm.writeLibraryConfigS('LJM_STREAM_RECEIVE_TIMEOUT_MS',0)  #disable timeout
        if self.deviceType == ljm.constants.dtT7:
            # self._command("STREAM_CLOCK_SOURCE", 0)  # enable internal clock
            aNames.append('STREAM_CLOCK_SOURCE')   # enable internal clock
            aValues.append(0)
        aNames.extend(["AIN_ALL_NEGATIVE_CH", "AIN0_RANGE", "AIN1_RANGE",
                  "STREAM_SETTLING_US", "STREAM_RESOLUTION_INDEX", 'STREAM_BUFFER_SIZE_BYTES'])
        n = np.ceil(np.log10(2*(1+max_samples))/np.log10(2))
        buffer_size = 2**n
        aValues.extend([ljm.constants.GND, 10.0, 10.0, 0, 0, buffer_size])
        self._write_array(aNames, aValues)
        self.stream_mode = 'in-triggered'

    def streamburst(self, duration, max_samples=2**13-1, operation = None):
        ''' Performs a burst stream and optionally performs a numpy array operation
            on the result.

            Args:
                duration (float): number of seconds to stream. Scan rate will be
                automatically adjusted to avoid overfilling the buffer.

                '''
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

    def prepare_stream_out(self, trigger = None):
        ''' Prepares an output stream.

            Args:
                trigger (int): if not None, set an FIO channel to trigger on

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

        if trigger is None:
            self._command("STREAM_TRIGGER_INDEX", 0)        # Ensure triggered stream is disabled.
            aNames = ['STREAM_TRIGGER_INDEX']
            aValues = [0]
        else:
            channel = 'DIO%i'%trigger
            aNames = ["%s_EF_ENABLE"%channel, "%s_EF_INDEX"%channel,
                      "%s_EF_OPTIONS"%channel, "%s_EF_VALUE_A"%channel,
                      "%s_EF_ENABLE"%channel, 'STREAM_TRIGGER_INDEX']
            aValues = [0, 3, 0, 2, 1, 2000+trigger]


        aNames.extend(["STREAM_SETTLING_US", "STREAM_RESOLUTION_INDEX"])
        aValues.extend([0, 0])
        if self.deviceType == ljm.constants.dtT7:
            aNames.append('STREAM_CLOCK_SOURCE')    # Enabling internally-clocked stream.
            aValues.append(0)
        self._write_array(aNames, aValues)
        self.stream_mode = 'out-triggered'

    def stream_out(self, channels, data, scanRate, loop = 0):
        ''' Streams data at a given scan rate. Currently only supports analog channels.

            Args:
                channels (list): Output channels to stream on, e.g. ['DAC0', 'DAC1']
                data (array): Data to stream out. For streaming on multiple channels, use column 0 for DAC0 and column 1 for DAC1.
                scanRate (float): desired output rate in scans/s
                loop (int): number of values from the end of the buffer to loop after finishing stream
        '''

        try:
            ''' Stop streaming if currently running '''
            ljm.eStreamStop(self.handle)
        except:
            pass
        n = np.ceil(np.log10(2*(1+len(data)))/np.log10(2))
        buffer_size = 2**n
        aScanList = []
        for i in range(len(channels)):
            aNames =["STREAM_OUT%i_TARGET"%i,
                           "STREAM_OUT%i_BUFFER_SIZE"%i,
                           "STREAM_OUT%i_ENABLE"%i]
            ch = channels[i]
            if ch == 'FIO_STATE':
                target = 2500
            else:
                target = 1000+2*ch
            aValues = [target, buffer_size, 1]
            self._write_array(aNames, aValues)
            if ch == 'FIO_STATE':
                target = ['STREAM_OUT%i_BUFFER_U16'%i]*len(data)
            else:
                target = ['STREAM_OUT%i_BUFFER_F32'%i] * len(data)
            try:
                target_array = data[:,i]
            except IndexError:
                target_array = data
            ljm.eWriteNames(self.handle, len(target_array), target, list(target_array))
            aNames = ["STREAM_OUT%i_LOOP_SIZE"%i,
                           "STREAM_OUT%i_SET_LOOP"%i]
            aValues = [loop*len(data), 1]
            self._write_array(aNames, aValues)
            aScanList.append(4800+i)

        scanRate = ljm.eStreamStart(self.handle, 1,len(aScanList), aScanList, scanRate)
        # log.info("\nStream started with a scan rate of %0.0f Hz." % scanRate)

    def sequence2stream(self, sequence, period, max_samples = None, channels = 1):
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
        if max_samples is None:
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

        # stream = np.zeros(int(samples))
        stream = np.zeros((int(samples), sequence.shape[1]))
        for i in range(sequence.shape[0]):
            for j in range(sequence.shape[1]):
                point = sequence[i,j]
                t = point[0]
                V = point[1]
                stream[int(t/period*samples)::, j] = V


        # for point in sequence:
        #     t = point[0]
        #     V = point[1]
        #     stream[int(t/period*samples)::] = V
        return stream, speed

    def resample(self, wave, period, max_samples = None, channels = 1):
        ''' Resamples a waveform with a given period into the optimal stream.

            Args:
                wave (array): An array of values describing a waveform.
                period (float): The total sequence duration.

            Returns:
                stream (array): A list of points which will be output at the calculated sampling rate.
                speed (float): Stream rate in samples/second.
        '''
        seq = []
        for i in range(wave.shape[0]):
            point = []
            for j in range(wave.shape[1]):
                t = i*period/len(wave)
                x = wave[i,j]
                point.append((t,x))
            seq.append(point)
        seq = np.array(seq)
        return self.sequence2stream(seq, period, max_samples, wave.shape[1])

if __name__ == '__main__':
    lj = LabJack(devid='470016973')
    sequence = [(0,0), (0.05,1)]
    period = .1
    stream, speed = lj.sequence2stream(sequence, period)
    lj.stream_out([0], stream, speed, trigger = 0)
    for i in range(100):
        lj.DOut(2,i%2)
