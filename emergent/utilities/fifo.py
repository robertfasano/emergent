''' This module implements a basic FIFO queue which allows messages to be simultaneously
    dispatched to the same device by EMERGENT without risking message overlap on the
    actual device.
'''
import queue
import logging as log

class Message():
    ''' Container for queue message-passing '''
    def __init__(self, ID, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.ID = ID

class FIFO(queue.Queue):
    ''' Implements a threaded queue which continuously executes commands in
        a FIFO order. '''
    def __init__(self):
        super().__init__()
        self.buffer = {}

    def add(self, func, ID, *args, **kwargs):
        ''' Adds a function with optional positional and keyword arguments to the queue. '''
        class NewMessage(Message):
            ''' A container for a queued function call. '''
            def run(self):
                ''' Return the function defined by the add() method. '''
                return func(*self.args)
        log.debug('Added %s to queue with ID %f.', func, ID)
        self.put(NewMessage(ID, *args, **kwargs))

    def next(self):
        ''' Retrieves and executes the next function on a FIFO basis. '''
        msg = self.get()
        result = msg.run()
        self.buffer[msg.ID] = result

    def run(self, stopped):
        ''' Continuously retrieve and execute the next task. '''
        while not stopped():
            self.next()
