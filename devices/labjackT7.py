from labjack import ljm
from random import randrange
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import scipy.signal as sig
from scipy.stats import linregress
import time
from threading import Thread
from archetypes.parallel import ProcessHandler

class LabJack(ProcessHandler):
    ''' Python interface for the LabJack T7. '''

    def __init__(self, device = "ANY", connection = "ANY", devid = "ANY", arange = 10):
        ''' Attempt to connect to a LabJack.

            Args:
                device (str): Device type ("ANY", "T7" are currently supported).
                connection (str): Desired connection type ("ANY", "USB", "TCP", "ETHERNET", or "WIFI").
                devid (str): Serial number, which can be found on the underside of the LabJack.
                arange (float): analog input range.'''
        super().__init__()
        self.device = device
        self.connection = connection
        self.devid = devid
        self.arange = arange
        self._connected = 0
        self.averaging_array = []
        self._connected = self._connect()

    def _connect(self):
        try:
            self.handle = ljm.openS(self.device, self.connection, self.devid)
            self._command('AIN_ALL_RANGE', self.arange)
            info = ljm.getHandleInfo(self.handle)
            print('Connected to LabJack (%i).'%(info[2]))
            self.clock = 80e6       # internal clock frequency
            deviceType = info[0]
            return 1
            if deviceType != ljm.constants.dtT7:
                print('Only the LabJack T7 is supported.')
                return 0

        except:
            print('Failed to connect to LabJack (%s).'%self.devid)

    def _command(self, register, value):
        ''' Writes a value to a specified register.

            Args:
                register (str): a Modbus register on the LabJack.
                value: the value to write to the register.
                '''
        ljm.eWriteName(self.handle, register, value)

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
            print(e)

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
    def stream_out(self, channel, data, loop = False):
        ''' Streams data at 100 kS/s.

            Args:
                channel (int): DAC channel to use. 0 for DAC0 or 1 for DAC1.
                data (array): Data to stream out.
                loop (bool): if False, data will be streamed out once; if True, the stream will loop.
        '''

        self._command("STREAM_OUT0_ENABLE", 0)
        self._command("STREAM_OUT0_TARGET", 1000+2*channel)
        self._command("STREAM_OUT0_BUFFER_SIZE", data.nbytes*2)
        self._command("STREAM_OUT0_ENABLE", 1)

        if loop:
            ljm.eWriteName(handle, "STREAM_OUT0_LOOP_SIZE", len(data))
            ljm.eWriteName(handle, "STREAM_OUT0_SET_LOOP", 1)

        ''' Add data to buffer '''
        self._command("STREAM_OUT0_BUFFER_F32", data)

        ''' Start stream '''
        self._command("STREAM_OUT0", 1)
