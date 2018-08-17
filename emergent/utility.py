import inspect
import importlib
import os
import datetime
import decorator

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
def cost(func, *args, **kwargs):
    c = func(*args, **kwargs)
    t = datetime.datetime.now()
    for full_name in args[0].inputs:
        args[0].update_dataframe(t, full_name, args[0].inputs[full_name].state)
    args[0].update_cost(t, c)

    return c

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

def get_args(cls, func):
    f = getattr(cls, func)
    ''' Read default params dict from source code and insert in self.params_edit. '''
    args = inspect.signature(f).parameters
