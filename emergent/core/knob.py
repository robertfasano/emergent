class knob(object):
    def __init__(self, name, fget=None, fset=None):
        self.name = name
        self.fget = fget
        self.fset = fset

    def __get__(self, obj, objtype=None):
        try:
            if not obj.simulation:
                val = self.fget(obj)
            else:
                val = obj.__dict__['_'+self.name]
            return val
        except AttributeError:
            return None

    def __set__(self, obj, value):
        ''' Calls the user-defined command. To avoid offloading boilerplate to the users,
            this method also updates the property value with the new signal. '''
        if not obj.simulation:
            self.fset(obj, value)
        obj.__dict__['_'+self.fset.__name__] = value
        if obj.hub is not None:
            obj.hub.state[obj.name][self.name] = value

    def command(self, fset):
        ''' Decorator method allowing simple definition of device commands. '''
        return type(self)(self.name, self.fget, fset)

    def query(self, fget):
        return type(self)(self.name, fget, self.fset)

def Knob(name):
    def getter(self):
        _name = '_%s'%name
        if hasattr(self, _name):
            return getattr(self, _name)
        else:
            setattr(self, _name, None)

    def setter(self, newval):
        _name = '_%s'%name
        if self.hub is not None:
            self.hub.state[self.name][name] = newval
        setattr(self, _name, newval)
    return knob(name, getter, setter)

def Sensor(name):
    def getter(self):
        _name = '_%s'%name
        return getattr(self, _name)

    def setter(self, newval):
        print("Sensor '%s.%s' value is read-only!"%(self.name, name))
    return knob(name, getter, setter)
