'''if the amplifiers are not working, then first unplug and reinsert the #1 +5V HV the pin once it is connected
and initialized; otherwise, ensure that 5 volts of power are being delivered to the board'''
import time
from labAPI.devices.labjackT7 import LabJack
import numpy as np
import sys
import os
char = {'nt': '\\', 'posix': '/'}[os.name]
sys.path.append(char.join(os.getcwd().split(char)[0:-2]))   
from labAPI.archetypes.Optimizer import Optimizer
from labAPI.archetypes.device import Device
#from simplex import Simplex
#
class PicoAmp(Device, Optimizer):
    def __init__(self, name = 'picoAmp', labjack = None):
        Device.__init__(self, name)
        Optimizer.__init__(self, None)
        self.state = 0
        self.addr = {}
        self.addr['A'] = '000'
        self.addr['B'] = '001'
        self.addr['C'] = '010'
        self.addr['D'] = '011'
        self.addr['ALL'] = '111'
        self.position = [self.params['X']['value'], self.params['Y']['value']]
        self.waitTime = 0.01            # time to sleep between moving and measuring
        if labjack == None:
            labjack = LabJack(devid='470016970')
        self.labjack = labjack
        if self.labjack._connected:
            self.labjack.spi_initialize(mode=0)
            self.connect()
            self.actuate([])
            

    def connect(self):
        ''' Initializes the DAC and sets the bias voltage on all four channels to 80 V. '''
        
        self.state = 1
        self.labjack.PWM(3, 49000, 50)
#        for pin in [17,18,21,22, 28, 29, 30, 31]:
#            os.system('config-pin p9.%i spi'%pin)
        FULL_RESET = '001010000000000000000001'    #2621441
        ENABLE_INTERNAL_REFERENCE =  '001110000000000000000001'     #3670017
        ENABLE_ALL_DAC_CHANNELS = '001000000000000000001111'      #2097167
        ENABLE_SOFTWARE_LDAC = '001100000000000000000001'    #3145728
        self.Vbias = 80.0
        biasString = self.digital(self.Vbias)
        
        # initialize board 0
#        self.spi0 = SPI(0,0)
#        spi.lsbfirst = False
        for cmd in [FULL_RESET, ENABLE_INTERNAL_REFERENCE, ENABLE_ALL_DAC_CHANNELS, ENABLE_SOFTWARE_LDAC]:
            self.command(cmd, 0)
        cmd = '00' + '011' + self.addr['ALL'] + biasString
        self.command(cmd, 0)
        
        # initialize board 1
#        self.spi1 = SPI(1,0)
##        spi.lsbfirst = False
#        for cmd in [FULL_RESET, ENABLE_INTERNAL_REFERENCE, ENABLE_ALL_DAC_CHANNELS, ENABLE_SOFTWARE_LDAC]:
#            self.command(cmd, 1)
#        cmd = '00' + '011' + self.addr['ALL'] + biasString
#        self.command(cmd, 1)
        
        # initialize the ADC
#        ADC.setup()
#        self.state = 1
        
    def actuate(self, pos):
        self.moveTo(pos)
        
    def cost(self):
        return self.readADC()
        
    def circle(self, radius=80):
        x = []
        y = []
        while True:
            for theta in np.linspace(0,2*np.pi,100):
                x = radius*np.cos(theta)
                y = radius*np.sin(theta)
                
                self.setDifferential(x, 'X', 0)
                self.setDifferential(y, 'Y', 0)
            
    def command(self, cmd, board, output = False):
        ''' Separates the bitstring cmd into a series of bytes and sends them through the SPI. '''
        if self.state:
            lst = []
            r = 0
            for i in [0, 8, 16]:
                lst.append(int(cmd[i:8+i],2))
            if board == 0:
#                r = self.spi0.xfer2(lst)
                r = self.labjack.spi_write(lst, verbose = False)
            elif board == 1:
                r = self.spi1.xfer2(lst)
            if output == True: 
                print(r)
        
    def digital(self, V):
        ''' Converts an analog voltage V to a 16-bit string for the DAC '''
        Range = 200.0
        Vdigital = V/Range * 65535
    
        return format(int(Vdigital), '016b')
    
    def maximize(self, axis, board):
        power = []
        self.averagingTime = 5
#        res = 20/2**16
#        step = 50*res
        step = 0.2

        # first check which direction to move by computing gradient
        checks = []
        
        self.step(-step, axis, board) 
        time.sleep(self.waitTime)
        checks.append(self.readADC(num=50))
        time.sleep(self.waitTime)
        
        self.step(step, axis, board) 
        time.sleep(self.waitTime)
        checks.append(self.readADC(num=50))
        time.sleep(self.waitTime)
        
        self.step(step, axis, board) 
        time.sleep(self.waitTime)
        checks.append(self.readADC(num=50))
        time.sleep(self.waitTime)
        
        direction = -1
        if np.mean(np.diff(checks)) > 0:
            direction = 1
        else:
            self.step(-step, axis, board)   # undo move in wrong direction
    
        lastNPoints = np.array([])
        movingDeriv = 0
        maximizing = True
        while maximizing:
            self.step(direction*step, axis, board) 
            time.sleep(self.waitTime)
            val = self.readADC() 
            power.append(val)
            lastNPoints = np.append(lastNPoints, val)
            if len(lastNPoints) > self.averagingTime:
                lastNPoints = np.delete(lastNPoints,0)
            if len(lastNPoints) > 1:
                movingDeriv = np.mean(np.diff(lastNPoints))
            if movingDeriv < 0 and len(lastNPoints) == self.averagingTime:
                maximizing = False
                numSteps = len(lastNPoints) - np.argmax(lastNPoints) - 1
                for i in range(numSteps):
                    self.step(-direction*step, axis, board)
                    val = self.readADC()
                    power.append(val)
                    
    def moveTo(self, pos):
        ''' Sets two-axis beam alignment according to differential voltages in the list pos. The first two elements
            correspond to board zero, the second two to board 1. '''
        self.setDifferential(pos[0], 'X', 0)
        self.setDifferential(pos[1], 'Y', 0)
        
        self.position = pos
        
    def readADC(self, pin=40, num = 1):
        ''' Analog input 0 on the BeagleBone is pin 39 on the P9 header. GNDA_ADC is pin 34.'''
        vals = []
        for i in range(num):
#            vals.append(ADC.read("P9_%i"%pin) * 1.8)
            vals.append(self.labjack.AIn(0))
#        print(np.mean(vals))
        return np.mean(vals)

    def setDifferential(self, V, axis, board):
        ''' Sets a target differential voltage V=HV_A-HV_B if axis is 'X' or V=HV_C-HV_D if axis is 'Y'.
            For example, if V=2 and  axis is 'X', this sets HV_A=81 and HV_2=79. 
            Allowed range of V is 0-160.'''
        V = float(V)
        V = np.clip(V, -80, 80)
        stringPlus = self.digital(self.Vbias+V)
        stringMinus = self.digital(self.Vbias-V)
        cmdPlus = 0
        cmdMinus = 0
        if axis == 'X':
            cmdPlus = '00' + '011' + self.addr['A'] + stringPlus
            cmdMinus = '00' + '011' + self.addr['B'] + stringMinus
        elif axis == 'Y':
            cmdPlus = '00' + '011' + self.addr['C'] + stringPlus
            cmdMinus = '00' + '011' + self.addr['D'] + stringMinus
        
        self.command(cmdPlus, board)
        self.command(cmdMinus, board)
        
    def sineWave(self, amplitude, frequency, axis='X', board=0):
        ''' Generates a sine wave with specified amplitude and frequency. The frequency
            is controlled by waiting after setting the position; because time.sleep() 
            cannot take a negative argument, I enforce a minimum wait of zero. Therefore,
            setting the frequency beyond the bandwidth of the code will not throw an error,
            but will have no effect. '''
#        x = np.linspace(0,2*np.pi,1000)
#        y = np.sin(x)
        steps = 100
        period = 1.0/float(frequency)
        dt = float(period) / float(steps)
        x = 0
        while True:
            try:
                t1 = time.time()
                self.setDifferential(amplitude*np.sin(x), axis, board)
                t2 = time.time()
#                print(dt-(t2-t1))
                time.sleep(np.max([dt-(t2-t1),0]))
                x += 2*np.pi/steps
            except KeyboardInterrupt:
                return
    
    def squareWave(self, amplitude, frequency, axis='X', board=0):
        ''' Generates a square wave with specified amplitude and frequency. '''
#        x = np.linspace(0,2*np.pi,1000)
#        y = np.sin(x)
        print('Generating square wave.')
        steps = 2
        period = 1.0/float(frequency)
        dt = float(period) / float(steps)
        sign = 1.0
        while True:
            try:
                t1 = time.time()
                self.setDifferential(amplitude*sign, axis, board)
                t2 = time.time()
#                print(dt-(t2-t1))
                time.sleep(np.max([dt-(t2-t1),0]))
                sign *= -1.0
            except KeyboardInterrupt:
                return           
               
    def step(self, s, axis, board):
        if axis == 'X' and board == 0:
            d = 0
        elif axis == 'Y' and board == 0:
            d = 1
        elif axis == 'X' and board == 1:
            d = 2
        elif axis == 'Y' and board == 1:
            d = 3
        target = self.position
        target[d] += s
        
        self.moveTo(target)
        
    def toggleState(self):
        self.state = (self.state+1)%2

        
def binary(string):
    return int(string, 2)


if __name__ == '__main__':
    pico = PicoAmp()
    pico.actuate([-60, 0])
#    pico.squareWave(80,2)     # aligned for differential amplitude of 80 V
#    pico.circle()
#    pico.moveTo([19.94,23.5,0,0])
#    pico.pwm(channel="P9_14")       # starts PWM on pins 12 and 14
#    x, y, V = pico.first_light(0, span=40, steps = 50)
#    pico.explore(0, span=1, steps = 10)

#    print(mems.readADC())
#    mems.thermalTesting()
#    mems.dither(0)

