import numpy as np
import time

def measure(source, channel):
    return np.random.uniform()

def TTL(source, channel):
    ''' Waits until a positive TTL signal appears on the given channel, then return '''
#    while measure(source, channel) < 2:
#        continue
    time.sleep(1)
