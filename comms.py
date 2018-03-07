import json
import requests
import multiprocessing
  
    
class Slack():
    def __init__(self, webhook):
        ''' A class for relaying messages between the code and Slack. Pass in a channel's webhook at initialization. '''
        self.webhook = webhook
        
    def send(self, message):
        ''' Sends a specified message to the webhook '''
        payload={"text": "%s"%message}
        requests.post(self.webhook, json=payload)
    
class Dweet():
    ''' A class for remote communication through the Dweet protocol. Pass in a unique guid at initialization. '''
    def __init__(self, guid):
        self.guid = guid
        
    def receive(self):
        url = 'https://dweet.io/get/latest/dweet/for/%s'%self.guid
        r = json.loads(requests.get(url).text)
        return r['with'][0]['content']
    
    def send(self, params, vals):
        ''' Sends a list of values for named parameters to a Dweet guid '''
        url = 'https://dweet.io/dweet/for/%s?'%self.guid
        for i in range(len(params)):
            url += '%s=%s&'%(params[i], vals[i])
        url = url[0:-1]
        print(url)
        r = json.loads(requests.get(url).text)
        
        return r
   
class DweetTransmitter(Dweet):
    ''' Sends dweets in real time from the last line of a file. '''
    def __init__(self, guid, filename):
        super.__init__(guid)
        self.filename = filename
    
    def start(self):
        self.transmitProcess = mp.Process(target = self.transmit)
        self.transmitProcess.start()
        
    def transmit(self):
        while True:
            with open(filename, 'r') as file:
                update = file.readlines[-1]
            
        
class DweetReceiver(Dweet):
    ''' Receives dweets in real time and allows logging and visualization. '''
    def __init__(self, guid):
        super.__init__(guid)

    
filename = 'O:\Public\\Yb clock\\180306\\twoClocksDifferenceExport_1.txt'