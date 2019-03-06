import time
import numpy as np
import logging as log
import pickle
import sys

def unit_test(self, func, *args, **kwargs):
    tests = 100
    times = []
    for i in range(tests):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        times.append(end-start)
    print(np.mean(times), '+/-', np.std(times))

class Timer():
    def __init__(self):
        self.times = [time.time()]

    def log(self, name = None):
        self.times.append(time.time())
        if name is not None:
            log.info('%s:%f'%(name, self.times[-1]-self.times[-2]))

class Profiler():

    @staticmethod
    def size(obj):
        return sys.getsizeof(pickle.dumps(obj))

    @staticmethod
    def profile(obj):
        try:
            d = obj.__getstate__()
        except AttributeError:
            d = obj.__dict__
        for item in d:
            print(item, sys.getsizeof(pickle.dumps(d[item])))
