<<<<<<< HEAD
import time
import numpy as np

=======
>>>>>>> 31803e2934583a9e7f1a5204f7bc537ac920e227
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
<<<<<<< HEAD
=======
        import time
>>>>>>> 31803e2934583a9e7f1a5204f7bc537ac920e227
        self.times = [time.time()]

    def log(self, name = None):
        self.times.append(time.time())
        if name is not None:
            log.info('%s:%f'%(name, self.times[-1]-self.times[-2]))
