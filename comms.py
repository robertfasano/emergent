import json
import requests
import time
    
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
        try:
            url = 'https://dweet.io/get/latest/dweet/for/%s'%self.guid
            r = json.loads(requests.get(url).text)

            j = r['with'][0]['content']
#            j['time'] = r['with'][0]['created']
            return j
        except KeyError:
            if r['because'] == 'Rate limit exceeded, try again in 1 second(s).':
                time.sleep(1.01)
                return self.receive()
            else:
                print(r)

        
    
    def send(self, params, vals):
        ''' Sends a list of values for named parameters to a Dweet guid '''
        url = 'https://dweet.io/dweet/for/%s?'%self.guid
        for i in range(len(params)):
            url += '%s=%s&'%(params[i], vals[i])
        url = url[0:-1]
        r = json.loads(requests.get(url).text)
        
        return r
   

    
if __name__ == '__main__':
    dev = Dweet('ybdatalogger12345')
    r = dev.receive()