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

def get_open_port():
    import socket
    s = socket.socket()
    s.bind(('', 0))            # Bind to a free port provided by the host.
    return s.getsockname()[1]  # Return the port number assigned.

def get_address():
    import socket
    return socket.gethostbyname(socket.gethostname())

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

def list_triggers(hub):
    ''' Returns a list of all methods tagged with the '@trigger' decorator '''
    return methodsWithDecorator(hub.__class__, 'trigger')

def list_experiments(hub):
    ''' Returns a list of all methods tagged with the '@experiment' decorator '''
    return methodsWithDecorator(hub.__class__, 'experiment')

def list_errors(hub):
    ''' Returns a list of all methods tagged with the '@error' decorator '''
    return methodsWithDecorator(hub.__class__, 'error')

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


def thing(func):
    return func

class Parameter():
    def __init__(self, name, value, min = None, max = None, description = ''):
        self.name = name
        self.value = value
        self.min = min
        self.max = max
        self.description = description


@decorator.decorator
def experiment(func, hub, sampler, state):
    results = []
    params = sampler.experiment_params
    ''' Check that all Watchdogs report lock state. If any fail, they will attempt
        to reacquire lock with the Watchdog.react() method '''
    if not sampler.skip_lock_check:
        hub.check_lock()
    for i in range(int(params['cycles per sample'])):
        if sampler.trigger is not None:
            sampler.trigger()
        c = func(hub, state, params)
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
    while not func(*args):
        continue

@decorator.decorator
def algorithm(func, *args, **kwargs):
    func(*args, **kwargs)
    args[0].sampler.hub.save()

@decorator.decorator
def servo(func, *args, **kwargs):
    func(*args, **kwargs)
    args[0].sampler.hub.save()

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

def import_thing(name):
    handle = get_classes('things', 'thing')[name]
    return handle

def create_thing(name):
    thing = import_thing(name)
    args = get_args(thing, '__init__')

def extract_pulses(data, threshold):
    ''' Splits a numpy array into segments which are above a threshold. '''
    data = np.array(data)
    return np.split(data, np.where(np.diff(data > threshold))[0] + 1)[1::2]

def get_args(cls, func):
    f = getattr(cls, func)
    ''' Read default params dict from source code and insert in self.algorithm_params_edit. '''
    args = inspect.signature(f).parameters

class MacroBuffer(list):
    def __init__(self, parent):
        super().__init__()
        self.length = 10
        self.index = -1
        self.parent = parent

    def add(self, state):
        if len(self) > 0:
            if state == self[-1]:
                return
            for i in range(self.index+1, 0):
                del self[i]
        self.append(state.copy())

        self.index = -1
        self.prune()

    def undo(self):
        if self.index-1 < -len(self):
            return
        last_state = self[self.index-1]
        if self.parent.node_type == 'input':
            self.parent.parent.actuate({self.parent.name: last_state})
        elif self.parent.node_type == 'thing':
            self.parent.parent.actuate({self.parent.name: last_state})
        elif self.parent.node_type == 'hub':
            self.parent.actuate(last_state)
        self.index -= 1
        self.prune()

    def redo(self):
        if self.index >= -1:
            return
        last_state = self[self.index+1]
        if self.parent.node_type == 'input':
            self.parent.parent.actuate({self.parent.name: last_state})
        elif self.parent.node_type == 'thing':
            self.parent.parent.actuate({self.parent.name: last_state})
        elif self.parent.node_type == 'hub':
            self.parent.actuate(last_state)
        self.index += 1
        self.prune()

    def prune(self):
        while len(self) > self.length:
            del self[0]

class StateBuffer(list):
    def __init__(self, parent):
        super().__init__()
        self.length = 10
        self.index = -1
        self.parent = parent

    def add(self, state):
        if len(self) > 0:
            if state == self[-1]:
                return
        for i in range(self.index+1, 0):
            del self[i]
        self.append(state.copy())

        self.index = -1
        self.prune()
    def undo(self):
        states = [self[i] for i in range(self.index, 0)]
        if self.index-1 < -len(self):
            return
        last_state = self[self.index-1]
        index = self.index
        self.index -= 1
        if self.parent.node_type == 'input':
            self.parent.parent.actuate({self.parent.name: last_state})
        elif self.parent.node_type == 'thing':
            self.parent.parent.actuate({self.parent.name: last_state})
        elif self.parent.node_type == 'hub':
            self.parent.actuate(last_state)
        del self[-1]        # don't add undo actuate to buffer
        self.extend(states)
        self.index = index - 1
        self.prune()

    def redo(self):
        states = [self[i] for i in range(self.index+1, 0)]
        if self.index >= -1:
            return
        last_state = self[self.index+1]
        index = self.index
        if self.parent.node_type == 'input':
            self.parent.parent.actuate({self.parent.name: last_state})
        elif self.parent.node_type == 'thing':
            self.parent.parent.actuate({self.parent.name: last_state})
        elif self.parent.node_type == 'hub':
            self.parent.actuate(last_state)
        del self[-1]        # don't add redo actuate to buffer
        self.index = index + 1
        self.extend(states)
        self.prune()

    def prune(self):
        while len(self) > self.length:
            del self[0]
