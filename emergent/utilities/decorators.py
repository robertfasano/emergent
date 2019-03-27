import decorator
import numpy as np
import time

@decorator.decorator
def thread(func, *args, **kwargs):
    new_thread = Thread(target=func, args=args, kwargs=kwargs)
    new_thread.start()

@decorator.decorator
def experiment(func, hub, state, params):
    return func(hub, state, params)

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
