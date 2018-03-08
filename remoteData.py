import IO
import comms
import pandas as pd
import multiprocessing as mp
import time
from threading import Thread
import numpy as np

class Transceiver(comms.Dweet):
    def __init__(self, guid, filename):
        super().__init__(guid)
        self.filename = filename
        
    def startTransmission(self):
#        self.transmitProcess = mp.Process(target = self.transmit)
#        self.transmitProcess.start()
        
        self.transmitThread = Thread(target=self.transmit)
        self.transmitThread.start()
        
    def transmit(self):
        while True:
#            with open(self.filename, 'r') as file:
#                params = IO.parseRow(file.readlines[0])
#                vals = IO.parseRow(file.readlines[1])
            params = ['time', 'mag_corr', 'bbq_corr']
            vals = [time.time(), np.random.uniform(), np.random.uniform()]
            self.send(params, vals)
            
    def listen(self):
        r = self.receive()
        self.cols = [x for x in r.keys() if x != 'time']
        self.data = pd.DataFrame(columns=self.cols)
        self.listenThread = Thread(target=self.get)
        self.listenThread.start()
            
    def get(self):
        while True:
            r = self.receive()
            if type(r) != int:
                for key in self.cols:
                    self.data.loc[r['time'],key] = r[key]
            
t = Transceiver('ybdatalogger12345', 'file.txt')
t.startTransmission()
t.listen()