def Knob(name):
    def getter(self):
        _name = '_%s'%name
        if hasattr(self, _name):
            return getattr(self, _name)
        # if _name in self.__dict__:
        #     print('getting')
        #     return self.__dict__[_name]
        else:
            # self.__dict__[_name] = None
            setattr(self, _name, None)
            self.knobs.append(name)

    def setter(self, newval):
        _name = '_%s'%name
        setattr(self, _name, newval)
        # self.__dict__[_name] = newval
    return property(getter, setter)
