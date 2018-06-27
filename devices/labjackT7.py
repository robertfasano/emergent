from labjack import ljm
from random import randrange
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import scipy.signal as sig
from scipy.stats import linregress
import time
from threading import Thread
from labAPI.archetypes.Parallel import ProcessHandler

class LabJack(ProcessHandler):
    def __init__(self, device = "ANY", connection = "ANY", devid = "ANY", orange = 10, arange = 10):
        super().__init__()
        self.device = device
        self.connection = connection
        self.devid = devid
        self.arange = arange
        self._connected = 0
        self.averaging_array = []
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
    
    def AOut(self, channel, value, prefix = 'DAC', HV=False):
        if not HV:
            ljm.eWriteName(self.handle, '%s%i'%(prefix, channel), value)
        else:
            ljm.eWriteName(self.handle, "TDAC%i"%channel, value)
    
    def PWM(self, channel, frequency, duty_cycle, handle = None):
        ''' Args:
                int channel: 0, 2-5 are valid for the LabJack T7
                float frequency
                float duty_cycle    '''
        try:
            if handle == None:
                handle = self.handle
            roll_value = self.clock / frequency
            config_a = duty_cycle * roll_value / 100
            ljm.eWriteName(handle, "DIO_EF_CLOCK0_ENABLE", 0);    # Disable the clock source
            ljm.eWriteName(handle, "DIO_EF_CLOCK0_DIVISOR", 1); 	# Configure Clock0's divisor
            ljm.eWriteName(handle, "DIO_EF_CLOCK0_ROLL_VALUE", roll_value); 	# Configure Clock0's roll value
            ljm.eWriteName(handle, "DIO_EF_CLOCK0_ENABLE", 1); 	# Enable the clock source
    
            # Configure EF Channel Registers:
            ljm.eWriteName(handle, "DIO%i_EF_ENABLE"%channel, 0); 	# Disable the EF system for initial configuration
            ljm.eWriteName(handle, "DIO%i_EF_INDEX"%channel, 0); 	# Configure EF system for PWM
            ljm.eWriteName(handle, "DIO%i_EF_OPTIONS"%channel, 0); 	# Configure what clock source to use: Clock0
            ljm.eWriteName(handle, "DIO%i_EF_CONFIG_A"%channel, config_a); 	# Configure duty cycle
            ljm.eWriteName(handle, "DIO%i_EF_ENABLE"%channel, 1); 	# Enable the EF system, PWM wave is now being outputted
        except Exception as e:
            print(e)
            
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

    def stream_start(self, channels, scanRate = 1000, target_rate = 100, clock = None, subtract_DC = False):
        ''' Currently supports only one channel, e.g. "AIN0" '''
        ''' Streams in data from target channel(s), which is optionally externally clocked on CIO3. '''
        self.scanCount = 0
#        ljm.writeLibraryConfigS("STREAM_SCANS_RETURN",1)     
#        ljm.writeLibraryConfigS("LJM_STREAM_RECEIVE_TIMEOUT", 0)
        
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
        scansPerRead = int(scanRate / target_rate / 1) 
#        scansPerRead = 1
                 
        ljm.eWriteName(self.handle, "STREAM_TRIGGER_INDEX", 0)

        # Write the inputs' negative channels, ranges, stream settling time, and resolution
        aNames = ["AIN_ALL_NEGATIVE_CH", "%s_RANGE"%channels,
                  "STREAM_SETTLING_US", "STREAM_RESOLUTION_INDEX"]
        aValues = [ljm.constants.GND, 10.0, 0, 0]
        ljm.eWriteNames(self.handle, len(aNames), aNames, aValues)
    
        # Configure and start stream
        scanRate = ljm.eStreamStart(self.handle, scansPerRead, numAddresses, aScanList, scanRate)
        print("\nStream started with a scan rate of %0.0f Hz." % scanRate)
        
#        plt.ion()
        self.fig = plt.figure()
        self.ax = plt.gca()
        plt.autoscale()
#        time.sleep(1)
        data = self.stream_read()
        self.averaging_window = 1
        data = self.stream_moving_average(data,n=self.averaging_window)
#        if subtract_DC:
#            data -= np.mean(data)
        # initialize highpass
        self.nyquist = scanRate / 2
#        self.sos = self.highpass_create(f0=.01)
#        data, self.zi = self.highpass_apply(self.sos, data, zi=None)
        if subtract_DC:
            data -= np.min(data)
            
            
        self.image, = self.ax.plot(data)
        self.ax.set_ylim([0,.1])
        self.subtract_DC = subtract_DC
        
            
        

        self.animation = animation.FuncAnimation(self.fig, self.stream_update, interval=0, blit=True)

            
    def stream_update(self, *args):
        data = self.stream_read()

        data = self.stream_moving_average(data, n=self.averaging_window)
#        data, self.zi = self.highpass_apply(self.sos, data, zi=self.zi)

        contrast = np.max(data) - np.min(data)
        contrast *= 10000
        contrast = int(contrast)
        
        self.scanCount += 1
        if self.scanCount % 250:
            with open('log.txt', 'a') as file:
                file.write('%i\n'%contrast)
            if self.subtract_DC:
                data -= np.min(data)

        N_avg = 1000
        self.averaging_array.append(contrast)
        if len(self.averaging_array) > N_avg:
            del self.averaging_array[0]
        print(int(np.mean(self.averaging_array)))
            
#        subset = data[data > np.mean(data)]
#        subset = subset[subset-np.mean(subset) < 3*np.std(subset)]
#        x = np.linspace(0,len(subset), len(subset))
#        fit = linregress(x, subset)
#        slope = fit[0]
#        error = fit[4]
#        print(slope/error)
        self.image.set_ydata(data)
        return self.image,

    def stream_moving_average(self, a, n=3) :
        ret = np.cumsum(a, dtype=float)
        ret[n:] = ret[n:] - ret[:-n]
        return ret[n - 1:] / n
    
    def stream_DSP(self, input_channel, output_channel, dsp, scanRate = 100000, targetRate = 100):
        ''' Streams in on input_channel, performs signal processing on the PC, then streams out on output_channel '''
        
        # Initialize input stream
        self.stream_start(input_channel, scanRate = scanRate, target_rate = targetRate)
        
        # start threaded DSP
        self.dsp_thread = Thread(target = self.stream_DSP_thread, args = (input_channel, output_channel, dsp, scanRate, targetRate))
        self.dsp_thread.start()
        
    def stream_DSP_thread(self, input_channel, output_channel, dsp, scanRate, targetRate):
        while True:
            data = self.stream_read()
            data = dsp(data)
            
    def highpass_apply(self, sos, data, zi = None):
        if zi is None:
            zi = np.zeros([np.shape(sos)[0],2])
        data, zi = sig.sosfilt(sos, data, zi = zi)
        return data, zi
    
    def highpass_create(self, f0):
        z,p,k = sig.ellip(12, 0.01, 100, f0, 'low', output = 'zpk')
        return sig.zpk2sos(z,p,k)
        
    def square_wave(self, channel, A, period, HV=False):
        self.sq_wave_thread = Thread(target=self.square_wave_thread, args=(channel, A, period, HV))
        self.sq_wave_thread.start()
        
    def square_wave_thread(self, channel, A, period, HV=False):
        state = 0
        while True:
            try:
                time.sleep(period/2)
                state = (state+1) % 2
                self.AOut(channel, A*state, HV=HV)
            except KeyboardInterrupt:
                return
            
    def stream_in_out(self, input_channel, output_channel, scanRate, targetRate, stopped = False): 
        ''' Stream data in on input_channel and out on output_channel '''
        OUT_NAMES = [output_channel]
        NUM_OUT_CHANNELS = len(OUT_NAMES)
        outAddress = ljm.nameToAddress(OUT_NAMES[0])[0]
        
        # Allocate memory for the stream-out buffer
        ljm.eWriteName(self.handle, "STREAM_OUT0_TARGET", outAddress)
        ljm.eWriteName(self.handle, "STREAM_OUT0_BUFFER_SIZE", 2**14)
        ljm.eWriteName(self.handle, "STREAM_OUT0_ENABLE", 1)
        
        ljm.eWriteName(self.handle, "STREAM_OUT0_SET_LOOP", 0)
                
        # Stream Configuration
        POS_IN_NAMES = [input_channel]
        NUM_IN_CHANNELS = len(POS_IN_NAMES)
        
        TOTAL_NUM_CHANNELS = NUM_IN_CHANNELS + NUM_OUT_CHANNELS
        
        # Add positive channels to scan list
        aScanList = ljm.namesToAddresses(NUM_IN_CHANNELS, POS_IN_NAMES)[0]
        scansPerRead = int(scanRate / targetRate)
        
        
        aScanList.extend([4800]) # Add the scan list outputs to the end of the scan list. 4800 = STREAM_OUT0

        ljm.eWriteName(self.handle, "STREAM_TRIGGER_INDEX", 0)        # Ensure triggered stream is disabled.
        ljm.eWriteName(self.handle, "STREAM_CLOCK_SOURCE", 0)       # Enabling internally-clocked stream.

        aNames = ["AIN_ALL_NEGATIVE_CH", "%s_RANGE"%input_channel,
                  "STREAM_SETTLING_US", "STREAM_RESOLUTION_INDEX"]
        aValues = [ljm.constants.GND, 10.0, 0, 0]
        numFrames = len(aNames)
        ljm.eWriteNames(self.handle, numFrames, aNames, aValues)
    
        scanRate = ljm.eStreamStart(self.handle, scansPerRead, TOTAL_NUM_CHANNELS, aScanList, scanRate)
        print("\nStream started with a scan rate of %0.0f Hz." % scanRate)
    
        while not stopped():
            try:
                ret = ljm.eStreamRead(self.handle)
                data = np.array(ret[0][0:(scansPerRead * NUM_IN_CHANNELS)])
#                data = ret[0]
                
                data = self.process_data(data)
                # Write values to the stream-out buffer
                target = ['STREAM_OUT0_BUFFER_F32'] * len(data)
                ljm.eWriteNames(self.handle, len(data), target, list(data))
            except KeyboardInterrupt:
                return
        
    def process_data(self, data):
        data = np.ones(len(data))*np.sum(data) / len(data)
        return data
        
        
        
if __name__ == '__main__':
    t7 = LabJack(devid='470016973')
    try:
        ljm.eStreamStop(t7.handle)
    except:
        pass
#    t7.stream_start('AIN0', clock='CIO3', scanRate = 100)
#    t7.stream_start('AIN0', scanRate = 100000, target_rate = 100, subtract_DC = True)
#    t7.stream_start('AIN0', scanRate = 100000, subtract_DC = True)
    t7.run_thread(target='stream_in_out',args=('AIN0', 'DAC0', 1000, 1))
#    t7.run_thread('PWM', args=(0,1,50))
#    t7.run_process('PWM', args=(0,1,50, t7.handle))
