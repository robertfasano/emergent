def __getstate__(self, ignore=[]):
    ''' When the pickle module attempts to serialize this object to file, it
        calls this method to obtain a dict to serialize. We intentionally omit
        any unpicklable objects from this dict to avoid errors. '''
    d = {}
    unpickled = []
    for item in ignore:
        if hasattr(self, item):
            unpickled.append(item)

    for item in self.__dict__:
        obj = getattr(self, item)
        if hasattr(obj, 'picklable'):
            if not obj.picklable:
                continue
        if item not in unpickled:
            d[item] = self.__dict__[item]
    return d
