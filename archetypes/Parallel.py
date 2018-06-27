import multiprocessing
import threading
class ProcessHandler():
    def __init__(self):
        self.threads = []
        
    def run_process(self, target, args = None):
        ''' Allows a target function of the parent object to be run in a process '''
        if type(target) == str:
            target = getattr(self, target)
        assert callable(target)
        Process(target=target, args=args, parent = self)
        
    def quit_process(self, target):
        if type(target) == str:
            target = getattr(self, target)
        assert callable(target)
        for thread in self.threads:
            if thread.target == target:
                thread.stop()
                
    def run_thread(self, target, args = None):
        ''' Allows a target function of the parent object to be run in a thread '''
        if type(target) == str:
            target = getattr(self, target)
        assert callable(target)
        Thread(target=target, args=args, parent = self)            
        
    def quit_thread(self, target, args = None):
        if type(target) == str:
            target = getattr(self, target)
        assert callable(target)
        for thread in self.threads:
            if thread.target == target:
                thread.stop()   
    
class Process(multiprocessing.Process):
    def __init__(self, target, args, parent):
        self.target = target
        if args is not None:
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
        if self in self.parent.threads:
            del self.parent.threads[self.parent.threads.index(self)]
        self.terminate()

class Thread(threading.Thread):
    def __init__(self, target, args, parent):
        self.target = target
        self._stopper = threading.Event()

        if args is not None:
            args = list(args)
            args.append(self.stopped)
            args = tuple(args)
            super().__init__(target=target, args = args)
        else: 
            args = (self.stopped)
            super().__init__(target=target, args = args)
            
        ''' Add process to parent '''
        self.parent = parent
        if not hasattr(self.parent, 'threads'):
            self.parent.threads = [self]
        else:
            self.parent.threads.append(self)
            
        self.start()
        
    def stop(self):
        if self in self.parent.threads:
            del self.parent.threads[self.parent.threads.index(self)]
        self._stopper.set()
        
    def stopped(self):
        return self._stopper.is_set()
    

        
    
class test_class(ProcessHandler):
    def __init__(self):
        super().__init__()
                
    def test_function(self):
        import time
        i=0
        while True:
            i += 1
            print(i)
            time.sleep(0.25)
            
if __name__ == '__main__':
    t = test_class()
    t.run_in_process('test_function')    
    
    