import queue

class Message():
    """abstract message class"""
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

class FIFO(queue.Queue):
    def __init__(self):
        super().__init__()

    def add(self, func, *args, **kwargs):
        ''' Adds a function with optional positional and keyword arguments to the queue. '''
        class msg(Message):
            def run(self):
                func(*self.args)
        self.put(msg(*args, **kwargs))


    def next(self):
        ''' Retrieves and executes the next function on a FIFO basis. '''
        msg = self.get()
        msg.run()

    def run(self, stopped):
        while not stopped():
            self.next()

if __name__ == '__main__':
    import decorator
    @decorator.decorator
    def add(func, *args, **kwargs):
        obj = args[0]
        getattr(obj, 'queue').add(func, *args, **kwargs)

    from emergent.archetypes.parallel import ProcessHandler
    class TestClass(ProcessHandler):
        def __init__(self):
            super().__init__()
            self.queue = FIFO()
            self._run_thread(self.queue.run)

        @add
        def foo(self, string):
            print(string)
    c = TestClass()
