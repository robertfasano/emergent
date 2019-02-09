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
        import time
        self.times = [time.time()]

    def log(self, name = None):
        self.times.append(time.time())
        if name is not None:
            log.info('%s:%f'%(name, self.times[-1]-self.times[-2]))
