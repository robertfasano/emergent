import inspect
import importlib
import os
import datetime
import decorator
import numpy as np
import time

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

def list_algorithms():
    ''' Returns a list of all methods tagged with the '@algorithm' decorator '''
    from emergent.archetypes.optimizer import Optimizer
    return methodsWithDecorator(Optimizer, 'algorithm')

def list_triggers(control):
    ''' Returns a list of all methods tagged with the '@trigger' decorator '''
    return methodsWithDecorator(control.__class__, 'trigger')

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

def dev(func):
    return func

@decorator.decorator
def experiment(func, *args, **kwargs):
    results = []
    params = args[2]
    for i in range(params['cycles per sample']):
        c = func(*args, **kwargs)
        results.append(c)
    c = np.mean(results)
    t = datetime.datetime.now()
    for dev_name in args[0].inputs:
        for input in args[0].inputs[dev_name]:
            args[0].update_dataframe(t, dev_name, input, args[0].inputs[dev_name][input].state)
    args[0].update_cost(t, c, func.__name__)

    return c

@decorator.decorator
def error(func, *args, **kwargs):
    control = args[0]
    state = args[1]
    devices = list(state.keys())
    dev = devices[0]
    inputs = list(state[dev].keys())
    input = inputs[0]
    input_node = control.children[dev].children[input]
    e = func(*args, **kwargs)
    input_node.error_history.loc[time.time()] = e
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
    ''' Read default params dict from source code and insert in self.params_edit. '''
    args = inspect.signature(f).parameters
