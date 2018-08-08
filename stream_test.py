from devices.labjackT7 import LabJack
import numpy as np
devid = '470016973'
port1 = None
port2 = None
labjack = LabJack(devid=devid)

''' Generate a waveform with specified period. Two limitations exist:
    the maximum sampling rate and the buffer size. A cutoff period determines which
    is sacrificed to maximize the other. '''
buffer_size = 2**14
max_samples = int(buffer_size/2)-1
max_speed = 100000
cutoff = max_samples / max_speed
period = cutoff

if period >= cutoff:
    samples = max_samples
    speed = samples/period
else:
    speed = max_speed
    samples = period*speed
    
x = np.linspace(0,2*np.pi, samples)
data = 2*np.abs(np.sin(x))
labjack.stream_out(0, data, speed)
