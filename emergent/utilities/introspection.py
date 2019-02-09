import inspect
import importlib
import os

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

def list_triggers(hub):
    ''' Returns a list of all methods tagged with the '@trigger' decorator '''
    return methodsWithDecorator(hub.__class__, 'trigger')

def list_experiments(hub):
    ''' Returns a list of all methods tagged with the '@experiment' decorator '''
    return methodsWithDecorator(hub.__class__, 'experiment')

def list_errors(hub):
    ''' Returns a list of all methods tagged with the '@error' decorator '''
    return methodsWithDecorator(hub.__class__, 'error')

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
