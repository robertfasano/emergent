import numpy as np
import time
import os
import sys
if os.name == 'posix':        # if using OS X, open a special testing version of the program
    sys.path.append('/Users/rjf2/Documents/GitHub')
else:
    sys.path.append('C:\\Users\\Public\\Documents\\GitHub')
    sys.path.append('C:\\Users\\Robbie\\Documents\\GitHub')
    import mcdaq
from labAPI.comms import Dweet

def measure(params=None, logic = 'mean'):
    ''' Args:
        params: dict containing three fields
            ADC: a member of some ADC class with a .read() method
            gate_time: averaging time in ms
            channel: the proper channel for the ADC
    '''
    vals = []
    if params['TTL'] != "None":
        while params['ADC'].read(params['TTL']) < 3:
            continue

    for i in range(int(params['gate_time'])):
        if params['ADC'] == None:
            vals.append(np.random.uniform())
        else:
            vals.append(params['ADC'].read(params['channel']))
    if logic == 'mean':
        return np.mean(vals)
    elif logic == 'max':
        return np.max(vals)
    

def TTL(params):
    ''' Waits until a positive TTL signal appears on the given channel, then return '''
    while measure(params, logic = 'max') < 3:
        continue

   
    
class MCDAQ(mcdaq.MCDAQ):
    def __init__(self, params):
        super().__init__(params['device'].encode(), params['id'].encode())
        self.AInputMode(mcdaq.Mode.DIFFERENTIAL)
        self.arange = mcdaq.Range.BIP20VOLTS
        
    def read(self, channel):
        return self.VIn(int(channel), self.arange)
    
def connect(adc):
    ''' A wrapper function which initializes an ADC of the desired type with the arguments contained in the params dict '''
    if adc['type'] == 'mcdaq':
        return MCDAQ(adc)
    if adc['type'] == 'remote':
        return Dweet(adc['id'])
    else:
        return None
    

    
    
        
