import numpy as np
from emergent.signals import WatchdogSignal

class Watchdog():
    def __init__(self, parent, name = 'watchdog'):
        self.parent = parent
        self.name = name
        self.threshold_type = 'lower'
        self.threshold = 1
        self.value = 0
        self.state = 0
        self.signal = WatchdogSignal()

    def check(self):
        ''' Private method which calls self.measure then updates the state '''
        print('Checking state of watchdog %s'%self.name)
        value = self.measure()
        print('Watchdog measures %f and compares to %f.'%(value, self.threshold))
        if self.threshold_type == 'upper':
            self.state = value < self.threshold
        elif self.threshold_type == 'lower':
            self.state = value > self.threshold
        if not self.state:
            print('Watchdog %s is reacting to an unlock!'%self.name)
            self.parent.locked = False
            self.react()
            self.parent.locked = True
        self.signal.emit(self.state)
        print('Watchdog %s is happy!'%self.name)

        return self.state

    def measure(self):
        return

    def react(self):
        return

if __name__ == '__main__':
    w = Watchdog()
