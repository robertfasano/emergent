from labjack import ljm
from random import randrange

class LabJack():
    def __init__(self, device = "ANY", connection = "ANY", devid = "ANY", orange = 10, arange = 10):
        self.device = device
        self.connection = connection
        self.devid = devid
        self.arange = arange
        self._connected = 0
        
        self._connect()
    def _connect(self):
        try:
            self.handle = ljm.openS(self.device, self.connection, self.devid)
            ljm.eWriteName(self.handle, 'AIN_ALL_RANGE', self.arange)
    
            info = ljm.getHandleInfo(self.handle)
            print("Opened a LabJack with Device type: %i, Connection type: %i,\n"
                  "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" %
                  (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))
            self.clock = 80e6       # internal clock frequency
            deviceType = info[0]
            self._connected = 1
            if deviceType != ljm.constants.dtT7:
                print('Only the LabJack T7 is supported.')
                self._connected = 0
                
        except:
            print('Failed to connect to LabJack (%s).'%self.devid)
            
        
            
    def AIn(self, channel):
        return ljm.eReadName(self.handle, 'AIN%i'%channel)
    
    def AOut(self, channel, value):
        return ljm.eWriteName(self.handle, 'DAC%i'%channel, value)
    
    def PWM(self, channel, frequency, duty_cycle):
        ''' Args:
                int channel: 0, 2-5 are valid for the LabJack T7
                float frequency
                float duty_cycle    '''
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
            
    def spi_initialize(self, mode = 3):  #, CS, CLK, MISO, MOSI):
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
        # Setting CS, CLK, MISO, and MOSI lines for the T7 and other non-T4 devices.
        ljm.eWriteName(self.handle, "SPI_CS_DIONUM", 1)  # CS is FIO1
        ljm.eWriteName(self.handle, "SPI_CLK_DIONUM", 0)  # CLK is FIO0
        ljm.eWriteName(self.handle, "SPI_MISO_DIONUM", 3)  # MISO is FIO3
        ljm.eWriteName(self.handle, "SPI_MOSI_DIONUM", 2)  # MOSI is FIO2
        
        ljm.eWriteName(self.handle, "SPI_MODE", mode)                  # Selecting Mode CPHA=1 (bit 0), CPOL=1 (bit 1)
        ljm.eWriteName(self.handle, "SPI_SPEED_THROTTLE", 0)        # Valid speed throttle values are 1 to 65536 where 0 = 65536 ~ 800 kHz
        ljm.eWriteName(self.handle, "SPI_OPTIONS", 0)               # Enabling active low clock select pin
        
    def spi_info(self):
        # Read back and display the SPI settings
        aNames = ["SPI_CS_DIONUM", "SPI_CLK_DIONUM", "SPI_MISO_DIONUM",
                  "SPI_MOSI_DIONUM", "SPI_MODE", "SPI_SPEED_THROTTLE",
                  "SPI_OPTIONS"]
        aValues = [0]*len(aNames)
        numFrames = len(aNames)
        aValues = ljm.eReadNames(self.handle, numFrames, aNames)
        
        print("\nSPI Configuration:")
        for i in range(numFrames):
            print("  %s = %0.0f" % (aNames[i],  aValues[i]))
        

    def spi_loopback(self):
        numBytes = 4
        dataWrite = []
        dataWrite.extend([randrange(0, 256) for _ in range(numBytes)])
        self.spi_write(dataWrite, verbose=True)
        self.spi_read(4, verbose=True)
        
    def spi_read(self, numBytes, verbose = False):
        # Read the bytes
        dataRead = ljm.eReadNameByteArray(self.handle, "SPI_DATA_RX", numBytes)
        ljm.eWriteName(self.handle, "SPI_GO", 1)
        
        if verbose:
            # Display the bytes read
            print("")
            for i in range(numBytes):
                print("dataRead[%i]  = %0.0f" % (i, dataRead[i]))
    
    def spi_write(self, data, verbose = False):
        # Write(TX)/Read(RX) 3 bytes
        numBytes = 3
        ljm.eWriteName(self.handle, "SPI_NUM_BYTES", numBytes)
        
        # Write the bytes
        ljm.eWriteNameByteArray(self.handle, "SPI_DATA_TX", len(data), data)
        ljm.eWriteName(self.handle, "SPI_GO", 1)  # Do the SPI communications
        
        if verbose:
            # Display the bytes written
            print("")
            for i in range(numBytes):
                print("dataWrite[%i] = %0.0f" % (i, data[i]))
        
    def stream_read(self):
        return ljm.eStreamRead(self.handle)[0]

    def stream_start(self, channels, scanRate = 1000, clock = None):
        ''' Currently supports only one channel, e.g. "AIN0" '''
        ''' Streams in data from target channel(s), which is optionally externally clocked on CIO3. '''
        ljm.eWriteName(self.handle, "LJM_STREAM_SCANS_RETURN", "LJM_STREAM_SCANS_ALL")     
        ljm.eWriteName(self.handle, "LJM_STREAM_RECEIVE_TIMEOUT_MS", 0)
        
        if clock != None:
            ljm.eWriteName(self.handle, "STREAM_CLOCK_SOURCE", 2)
            ljm.eWriteName(self.handle, "STREAM_EXTERNAL_CLOCK_DIVISOR", 1)
        else:
            ljm.eWriteName(self.handle, "STREAM_CLOCK_SOURCE", 0)

        # Stream Configuration
        if type(channels) == str:
            aScanListNames = [channels]
        elif type(channels) == list:
            aScanListNames = channels
        else:
            print('Invalid channel specification.')
            return
        numAddresses = len(aScanListNames)
        aScanList = ljm.namesToAddresses(numAddresses, aScanListNames)[0]
        scansPerRead = int(scanRate / 2)
                 
        # Ensure triggered stream is disabled.
        ljm.eWriteName(self.handle, "STREAM_TRIGGER_INDEX", 0)

        # Write the inputs' negative channels, ranges, stream settling time, and resolution
        aNames = ["AIN_ALL_NEGATIVE_CH", "%s_RANGE"%channels,
                  "STREAM_SETTLING_US", "STREAM_RESOLUTION_INDEX"]
        aValues = [ljm.constants.GND, 10.0, 0, 0]
        ljm.eWriteNames(self.handle, len(aNames), aNames, aValues)
    
        # Configure and start stream
        scanRate = ljm.eStreamStart(self.handle, scansPerRead, numAddresses, aScanList, scanRate)
        print("\nStream started with a scan rate of %0.0f Hz." % scanRate)

            
if __name__ == '__main__':
    t7 = LabJack()