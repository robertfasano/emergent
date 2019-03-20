import decorator
import numpy as np
import time
import logging as log

@decorator.decorator
def thread(func, *args, **kwargs):
    new_thread = Thread(target=func, args=args, kwargs=kwargs)
    new_thread.start()

from abc import abstractmethod
class Experiment():
    def __init__(self, sampler):
        self.sampler = sampler
        self.hub = sampler.hub

    def _run(self):
        params = sampler.experiment_params
        if not sampler.skip_lock_check:
            self.hub._check_lock()
        if 'cycles per sample' not in params:
            params['cycles per sample'] = 1
        for i in range(int(params['cycles per sample'])):
            if self.sampler.trigger is not None:
                self.sampler.trigger()
            c = self.run(state, params)
            results.append(c)

        c = np.mean(results)
        error = None
        if len(results) > 1:
            error = np.std(results)/np.sqrt(len(results))

        return c, error

    @abstractmethod
    def run(self):
        return

    @abstractmethod
    def prepare(self):
        return

    @abstractmethod
    def analyze(self, data):
        return data

@decorator.decorator
def experiment(func, hub, sampler, state):
    log.warn('Experiment decorator is deprecated; please use the new Experiment class')
    results = []
    params = sampler.experiment_params
    ''' Check that all Watchdogs report lock state. If any fail, they will attempt
        to reacquire lock with the Watchdog.react() method '''
    if not sampler.skip_lock_check:
        hub._check_lock()
    if 'cycles per sample' not in params:
        params['cycles per sample'] = 1
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

@decorator.decorator
def queue(func, *args, **kwargs):
    obj = args[0]
    id = time.time()
    q = getattr(obj, 'queue')
    q.add(func, id, *args, **kwargs)
    while True:
        try:
            return q.buffer[id]
        except KeyError:
            continue
