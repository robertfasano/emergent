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
        ''' Attempt to connect to the LabJack specified by device, connection, and
            devid args. '''
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
            ljm.eWriteName(self.handle, 'AIN_ALL_RANGE', self.arange)
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

    def AIn(self, channel, num = 1):
        ''' Read the specified channel. If num>1, multiple measurements are
            performed and averaged. '''
        vals = []
        for i in range(num):
            vals.append(ljm.eReadName(self.handle, 'AIN%i'%channel))
        return np.mean(vals)

    def AOut(self, channel, value, HV=False):
        ''' Output value (0-5V) on the specified channel. The HV flag allows the
            LJTick-DAC addon board to be used to generate +/-10V. '''
        if not HV:
            ljm.eWriteName(self.handle, '%s%i'%('DAC', channel), value)
        else:
            ljm.eWriteName(self.handle, "TDAC%i"%channel, value)

    def PWM(self, channel, frequency, duty_cycle):
        ''' Pulse width modulation on a channel (0 or 2-5) at a given frequency
            in Hz and duty cycle (0-1). '''
        try:
            roll_value = self.clock / frequency
            config_a = duty_cycle * roll_value / 100
            ljm.eWriteName(self.handle, "DIO_EF_CLOCK0_ENABLE", 0);    # Disable the clock source
            ljm.eWriteName(self.handle, "DIO_EF_CLOCK0_DIVISOR", 1); 	# Configure Clock0's divisor
            ljm.eWriteName(self.handle, "DIO_EF_CLOCK0_ROLL_VALUE", roll_value); 	# Configure Clock0's roll value
            ljm.eWriteName(self.handle, "DIO_EF_CLOCK0_ENABLE", 1); 	# Enable the clock source

            # Configure EF Channel Registers:
            ljm.eWriteName(self.handle, "DIO%i_EF_ENABLE"%channel, 0); 	# Disable the EF system for initial configuration
            ljm.eWriteName(self.handle, "DIO%i_EF_INDEX"%channel, 0); 	# Configure EF system for PWM
            ljm.eWriteName(self.handle, "DIO%i_EF_OPTIONS"%channel, 0); 	# Configure what clock source to use: Clock0
            ljm.eWriteName(self.handle, "DIO%i_EF_CONFIG_A"%channel, config_a); 	# Configure duty cycle
            ljm.eWriteName(self.handle, "DIO%i_EF_ENABLE"%channel, 1); 	# Enable the EF system, PWM wave is now being outputted
        except Exception as e:
            print(e)

    def spi_initialize(self, mode = 3, CLK=0, CS=1,MOSI=2, MISO=3):  #, CS, CLK, MISO, MOSI):
        ''' Args:
            int CS: the channel to use as chip select
            int CLK: the channel to use as the clock
            int MISO: the channel to use for input
            int MOSI: the channel to use for output
            '''
        """
        You can short MOSI to MISO for testing.

        T7:
            MOSI    FIO2
            MISO    FIO3
            CLK     FIO0
            CS      FIO1


        If you short MISO to MOSI, then you will read back the same bytes that you
        write.  If you short MISO to GND, then you will read back zeros.  If you
        short MISO to VS or leave it unconnected, you will read back 255s.

        """
        ljm.eWriteName(self.handle, "SPI_CS_DIONUM", CS)
        ljm.eWriteName(self.handle, "SPI_CLK_DIONUM", CLK)
        ljm.eWriteName(self.handle, "SPI_MISO_DIONUM", MISO)
        ljm.eWriteName(self.handle, "SPI_MOSI_DIONUM", MOSI)
        ljm.eWriteName(self.handle, "SPI_MODE", mode)                  # Selecting Mode CPHA=1 (bit 0), CPOL=1 (bit 1)
        ljm.eWriteName(self.handle, "SPI_SPEED_THROTTLE", 0)        # Valid speed throttle values are 1 to 65536 where 0 = 65536 ~ 800 kHz
        ljm.eWriteName(self.handle, "SPI_OPTIONS", 0)               # Enabling active low clock select pin

    def spi_write(self, data, verbose = False):
        ''' Writes a list of commands via SPI. '''
        numBytes = len(data)
        ljm.eWriteName(self.handle, "SPI_NUM_BYTES", numBytes)

        # Write the bytes
        ljm.eWriteNameByteArray(self.handle, "SPI_DATA_TX", len(data), data)
        ljm.eWriteName(self.handle, "SPI_GO", 1)  # Do the SPI communications

        if verbose:
            # Display the bytes written
            print("")
            for i in range(numBytes):
                print("dataWrite[%i] = %0.0f" % (i, data[i]))
