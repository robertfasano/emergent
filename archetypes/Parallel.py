import multiprocessing
        
class Process(multiprocessing.Process):
    def __init__(self, target, args, parent, singular = True):
        self.target = target
        if args is not None:
            super().__init__(target=target, args = args)
        else: 
            super().__init__(target=target)
            
        ''' Add process to parent '''
        self.parent = parent
        ''' If singular = True, only one instance of this function can be running.
            Check if any threads in the parent are running this yet. '''
        if singular:
            if hasattr(self.parent, 'threads'):
                for thread in self.parent.threads:
                    if thread.target == self.target:
                        return 

        if not hasattr(self.parent, 'threads'):
            self.parent.threads = [self]
        else:
            self.parent.threads.append(self)
            
        self.start()
        
    def stop(self):
        if self in self.parent.threads:
            del self.parent.threads[self.parent.threads.index(self)]
        self.terminate()
        
        
''' Below is a test function demonstrating how singular processes can be implemented without requiring
    additional functions to start the process in. Once the test_function.run() is started, it can be stopped
    by calling test_function.threads[0].stop(), which deletes the Process from the threads list and terminates
    the process.'''
class test_function():
    def test_function(self):
        ''' Check if thread for this function is currently running; if not, start it '''
        process = Process(target = self.test_function, args = None, parent = self, singular = True)
        if not process.is_alive():
            import time
            i=0
            while True:
                i += 1
                print(i)
                time.sleep(0.25)
    
if __name__ == '__main__':
    t = test_function()
    t.test_function()
    
    
    