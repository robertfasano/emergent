import decorator
import numpy as np
import time

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
