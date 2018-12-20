import numpy as np

class Watchdog():
    def __init__(self):
        self.threshold_type = 'upper'
        self.threshold = 1
        self.value = 0
        self.state = 0

    def _measure(self):
        ''' Private method which calls self.measure then updates the state '''
        value = self.measure()
        if self.threshold_type == 'upper':
            self.state = value < self.threshold
        elif self.threshold_type == 'lower':
            self.state = value > self.threshold
        print(value, self.state)

    def measure(self):
        return np.random.uniform(0, 2)

if __name__ == '__main__':
    w = Watchdog()
