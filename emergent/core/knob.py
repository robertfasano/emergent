'''
This module contains classes and methods for the property-based device state
representation. This is based around the @knob decorator.

'''
class knob(object):
    ''' Tagging a method with @knob constructs a property. The property can be read by
        accessing its class attribute, e.g. device.x, and set in the usual way, device.x=y.
        The command() and query() methods allow implementation of user-defined device
        communications. Tagging a method with x.command will execute the command before setting x,
        while tagging with x.query will request and return a state from the device. '''
    def __init__(self, name, getter=None, setter=None):
        self.name = name
        self.getter = getter
        self.setter = setter

    def __get__(self, obj, objtype=None):
        try:
            if not obj.simulation:
                val = self.getter(obj)
            else:
                val = obj.__dict__['_'+self.name]
            return val
        except AttributeError:
            return None

    def __set__(self, obj, value):
        ''' Calls the user-defined command. To avoid offloading boilerplate to the users,
            this method also updates the property value with the new signal. '''
        if not obj.simulation:
            self.setter(obj, value)
        obj.__dict__['_'+self.setter.__name__] = value
        if obj.hub is not None:
            obj.hub.state[obj.name][self.name] = value

    def command(self, setter):
        ''' Command methods are used to send device commands before updating the internal
            state representation. '''
        return type(self)(self.name, None, setter)

    def query(self, getter):
        ''' Query methods are used to request the current state from the device
            (as opposed to returning the last device set by EMERGENT). Supposing
            we have a property x, the decorator @x.query is used to construct a new
            instance of the property and call __get__ using the tagged method. '''
        return type(self)(self.name, getter, None)

def Knob(name):
    ''' Convenience function for constructing properties with default getter/setter behavior. '''
    def getter(self):
        ''' Default getter: if tagging a method device.x(), returns device._x.'''
        _name = '_%s'%name
        if hasattr(self, _name):
            return getattr(self, _name)
        else:
            setattr(self, _name, None)

    def setter(self, newval):
        ''' Default setter: if tagging a method device.x(), sets device._x. '''
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
