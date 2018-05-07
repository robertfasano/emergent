import numpy as np
import serial
import datetime
import time
from labAPI import protocols
class Sprout():
    def __init__(self):
        self.responseTime = 0
        self.idleToOnTime = 60
        self.warmupTimestep = 30
        self.numWarmupSteps = 100
        self.connect()
        
    def connect(self):
        try:
            self.serial = protocols.serial.Serial(port = 'COM7')

        except serial.serialutil.SerialException:
            self.serial.close()
            self.serial = protocols.serial.Serial(port = 'COM7')           
           
    def warmup(self):
        # determine which mode laser is in
        self.mode = self.askMode()
        print('Here we go')
        print(self.mode)
        if self.mode == 'OFF':
            self.setMode('IDLE')
            print('Set mode to IDLE')
            with open('C:\\Users\\yblab\\Desktop\\warmup_logfile.txt', 'a') as outfile:
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                outfile.write('%s\t MODE=IDLE\n'%(now))
                outfile.flush()
                self.mode == 'IDLE'
            time.sleep(self.idleToOnTime)
        self.mode = self.askMode()
        if self.mode == 'IDLE':
            self.setMode('ON')
            print('Set mode to ON')
            with open('C:\\Users\\yblab\\Desktop\\warmup_logfile.txt', 'a') as outfile:
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                outfile.write('%s\t MODE=ON\n'%(now))
                outfile.flush()
        powers = np.linspace(0.1, 18, self.numWarmupSteps)
        for power in powers:
            time.sleep(self.warmupTimestep)
            self.setPower(power)
            with open('C:\\Users\\yblab\\Desktop\\warmup_logfile.txt', 'a') as outfile:
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                outfile.write('%s\t%f\n'%(now,power))
                outfile.flush()
        
    def askPower(self):
        power = self.serial.command('POWER?')
        return float(power)
    
    def askMode(self):
        self.mode = self.serial.command('OPMODE?')
        return self.mode
        
    def setMode(self, mode):
        ''' Sets the operational mode of the Sprout.
            Arguments:
                mode (str): either 'OFF', 'ON', or 'IDLE'
        '''
        self.serial.command('OPMODE=%s'%mode)
    
    def setPower(self, power):
        ''' Sets the power of the Sprout.
            Arguments:
                power (float)
        '''
        if power < 0.1:
            power = 0.1          # minimum power of the Sprout is 0.1 W
        self.serial.command('POWER SET=%.2f'%power)
        print('Set power to %f'%power)
        
        
sprout = Sprout()
if sprout.ser.isOpen():
    with open('C:\\Users\\yblab\\Desktop\\warmup_logfile.txt', 'a') as outfile:
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        outfile.write('%s\tCONNECTED\n'%now)
try:
    with open('C:\\Users\\yblab\\Desktop\\warmup_logfile.txt', 'a') as outfile:
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        outfile.write('%s\tPOWER=%f\n'%(now,sprout.askPower()))
except Exception as e:
    with open('C:\\Users\\yblab\\Desktop\\warmup_logfile.txt', 'a') as outfile:
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        outfile.write('%s\tEXCEPTION: %s\n'%(now,e))
sprout.warmup()
sprout.ser.close()
if not sprout.ser.isOpen():
    with open('C:\\Users\\yblab\\Desktop\\warmup_logfile.txt', 'a') as outfile:
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        outfile.write('%s\tSERIAL CONNECTION CLOSED\n'%now)
        



    