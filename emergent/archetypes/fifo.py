import queue
import time

class Message():
    """abstract message class"""
    def __init__(self, id, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.id = id

class FIFO(queue.Queue):
    def __init__(self):
        super().__init__()
        self.buffer = {}

    def add(self, func, id, *args, **kwargs):
        ''' Adds a function with optional positional and keyword arguments to the queue. '''
        class msg(Message):
            def run(self):
                return func(*self.args)
        self.put(msg(id, *args, **kwargs))


    def next(self):
        ''' Retrieves and executes the next function on a FIFO basis. '''
        msg = self.get()
        r = msg.run()
        self.buffer[msg.id] = r

    def run(self, stopped):
        while not stopped():
            self.next()

if __name__ == '__main__':
    import decorator
    @decorator.decorator
    def wait(func, *args, **kwargs):
        obj = args[0]
        id = time.time()
        q = getattr(obj, 'queue')
        q.add(func, id, *args, **kwargs)
        while True:
            try:
                return q.buffer[id]
            except KeyError:
                continue

    from emergent.archetypes.parallel import ProcessHandler
    class TestClass(ProcessHandler):
        def __init__(self):
            super().__init__()
            self.queue = FIFO()
            self._run_thread(self.queue.run)

        @wait
        def foo(self, string):
            return string
    c = TestClass()
