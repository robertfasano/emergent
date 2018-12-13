import inspect
import importlib
import os
import datetime
import decorator
import numpy as np
import time
import logging as log

def unit_test(self, func, *args, **kwargs):
    tests = 100
    times = []
    for i in range(tests):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        times.append(end-start)
    print(np.mean(times), '+/-', np.std(times))

def getChar():
    ''' Returns a user-input keyboard character. Cross-platform implementation
        credited to Matthew Strax-Haber (StackExchange) '''
    # figure out which function to use once, and store it in _func
    if "_func" not in getChar.__dict__:
        try:
            # for Windows-based systems
            import msvcrt # If successful, we are on Windows
            getChar._func=msvcrt.getch

        except ImportError:
            # for POSIX-based systems (with termios & tty support)
            import tty, sys, termios # raises ImportError if unsupported

            def _ttyRead():
                fd = sys.stdin.fileno()
                oldSettings = termios.tcgetattr(fd)

                try:
                    tty.setcbreak(fd)
                    answer = sys.stdin.read(1)
                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, oldSettings)

                return answer

            getChar._func=_ttyRead

    return getChar._func()

def list_triggers(control):
    ''' Returns a list of all methods tagged with the '@trigger' decorator '''
    return methodsWithDecorator(control.__class__, 'trigger')

def list_experiments(control):
    ''' Returns a list of all methods tagged with the '@experiment' decorator '''
    return methodsWithDecorator(control.__class__, 'experiment')

def list_errors(control):
    ''' Returns a list of all methods tagged with the '@error' decorator '''
    return methodsWithDecorator(control.__class__, 'error')

def methodsWithDecorator(cls, decoratorName):
    methods = []
    sourcelines = inspect.getsourcelines(cls)[0]
    for i,line in enumerate(sourcelines):
        line = line.strip()
        if line.split('(')[0].strip() == '@'+decoratorName: # leaving a bit out
            nextLine = sourcelines[i+1]
            name = nextLine.split('def')[1].split('(')[0].strip()
            methods.append(name)
    return methods

class Timer():
    def __init__(self):
        import time
        self.times = [time.time()]

    def log(self, name = None):
        self.times.append(time.time())
        if name is not None:
            log.info('%s:%f'%(name, self.times[-1]-self.times[-2]))


def dev(func):
    return func

class Parameter():
    def __init__(self, name, value, min, max, description):
        self.name = name
        self.value = value
        self.min = min
        self.max = max
        self.description = description

@decorator.decorator
def experiment(func, *args, **kwargs):
    results = []
    params = args[2]
    for i in range(int(params['cycles per sample'])):
        c = func(*args, **kwargs)
        results.append(c)
    c = np.mean(results)
    error = None
    if len(results) > 1:
        error = np.std(results)/np.sqrt(len(results))

    return c, error

@decorator.decorator
def error(func, *args, **kwargs):
    e = func(*args, **kwargs)
    return e

@decorator.decorator
def trigger(func, *args, **kwargs):
    ''' Wait until the passed function returns True before proceeding. '''
    while not func():
        continue

@decorator.decorator
def algorithm(func, *args, **kwargs):
    func(*args, **kwargs)
    args[0].parent.save(tag='optimize')

@decorator.decorator
def servo(func, *args, **kwargs):
    func(*args, **kwargs)
    args[0].parent.save(tag='servo')

def get_classes(directory, decoratorName):
    classes = {}
    mod = importlib.import_module(directory)
    files = [x for x in os.listdir(directory) if not x.startswith('__')]

    for file in files:
        submodule = getattr(mod, file.split('.')[0])
        sourcelines = inspect.getsourcelines(submodule)[0]
        for i,line in enumerate(sourcelines):
            line = line.strip()
            if line.split('(')[0].strip() == '@'+decoratorName:
                nextLine = sourcelines[i+1]
                name = nextLine.split('class')[1].split('(')[0].strip()
                handle = getattr(submodule, name)
                classes[name]=handle

    return classes

def import_device(name):
    handle = get_classes('devices', 'dev')[name]
    return handle

def create_device(name):
    dev = import_device(name)
    args = get_args(dev, '__init__')

def extract_pulses(data, threshold):
    ''' Splits a numpy array into segments which are above a threshold. '''
    data = np.array(data)
    return np.split(data, np.where(np.diff(data > threshold))[0] + 1)[1::2]

def get_args(cls, func):
    f = getattr(cls, func)
    ''' Read default params dict from source code and insert in self.algorithm_params_edit. '''
    args = inspect.signature(f).parameters
