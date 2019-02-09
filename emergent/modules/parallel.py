''' This module implements a convenient framework for parallelizing code with either
    the multiprocessing or threading modules. The _run_thread() and _run_process()
    methods allow for one-line parallelization as well as tracking all running
    threads/processes for easy termination.
'''
import multiprocessing
import threading
class ProcessHandler():
    ''' A task manager allowing functions to be started and stopped in processes or threads. '''
    def __init__(self):
        ''' Initializes the ProcessHandler with no threads. '''
        self.threads = []
        self.processes = []
        self.picklable = False
        
    def _run_process(self, func, args = None):
        ''' Instantiates and starts a process running a target function.

            Note:
                Processes do not share memory with the rest of the code, so they must be entirely self-contained.
            Args:
                func (function/str): target function to run in process. Can also pass a string matching the function name.
                args (tuple): arguments to be passed in to func
            '''
        if type(func) == str:
            func = getattr(self, func)
        assert callable(func)
        Process(target=func, args=args, parent = self)

    def _quit_process(self, target):
        ''' Terminates a process by looking for the first running process in
            self.processes matching the target function and stopping it.

            Args:
                target (function/str): function or string matching function name
            '''
        if type(target) == str:
            target = getattr(self, target)
        assert callable(target)
        for thread in self.processes:
            if thread.target == target:
                thread.stop()

    def _run_thread(self, target, args = None, stoppable = True):
        ''' Instantiates and starts a thread running a target function.

            Note:
                Threads can share memory freely with the rest of the code.

            Note:
                The ``stoppable`` flag allows early termination of functions. To properly implement a stoppable threaded function, the main loop of the function should be executed inside a ``while not stopped():`` statement.
            Args:
                target (function/str): target function to run in thread. Can also pass a string matching the function name.
                args (tuple): arguments to pass into func
                stoppable (bool): whether or not we should allow early termination of the Thread
            '''
        if type(target) == str:
            target = getattr(self, target)
        assert callable(target)
        Thread(target=target, args=args, parent = self, stoppable = stoppable)

    def _quit_thread(self, target):
        ''' Terminates a thread by looking for the first running thread in self.threads
            matching the target function and stops it.

            Warning:
                Stopping a thread can have unintended consequences, as threads share memory with the rest of the code.
            Args:
                target (function/str): function or string matching function name
        '''
        if type(target) == str:
            target = getattr(self, target)
        assert callable(target)
        for thread in self.threads:
            if thread.target == target:
                thread.stop()

class Process(multiprocessing.Process):
    ''' Inherits from multiprocessing.Process to provide streamlined, intuitive
        process instantiation and termination. '''
    def __init__(self, target, args, parent):
        ''' Creates and starts a process running the target function and
        registers it with the parent ProcessHandler. '''
        self.target = target
        if args is not None:
            super().__init__(target=target, args = args)
        else:
            super().__init__(target=target)

        ''' Add process to parent '''
        self.parent = parent
        if not hasattr(self.parent, 'processes'):
            self.parent.processes = [self]
        else:
            self.parent.processes.append(self)

        self.start()

    def stop(self):
        ''' Terminates the process. '''
        if self in self.parent.processes:
            del self.parent.processes[self.parent.processes.index(self)]
        self.terminate()

class Thread(threading.Thread):
    ''' Inherits from threading.Thread to provide streamlined, intuitive
        thread instantiation and termination. '''
    def __init__(self, target, args, parent, stoppable = True):
        ''' Creates and starts a thread running the target function and
            registers it with the parent ProcessHandler. '''
        self.target = target
        self._stopper = threading.Event()

        if args is not None:
            args = list(args)
            if stoppable:
                args.append(self.stopped)
            args = tuple(args)
            super().__init__(target=target, args = args)
        else:
            if stoppable:
                args = (self.stopped,)
                super().__init__(target=target, args = args)
            else:
                super().__init__(target=target)

        ''' Add process to parent '''
        self.parent = parent
        if not hasattr(self.parent, 'threads'):
            self.parent.threads = [self]
        else:
            self.parent.threads.append(self)

        self.start()

    def stop(self):
        ''' Sets self._stopper to True, such that self.stopped() will yield
            True and trigger early termination within the target function. '''
        if self in self.parent.threads:
            del self.parent.threads[self.parent.threads.index(self)]
        self._stopper.set()

    def stopped(self):
        ''' Returns a boolean check for stoppable Threads. '''
        return self._stopper.is_set()
