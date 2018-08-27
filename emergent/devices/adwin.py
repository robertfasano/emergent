


class ADwinPro():
    def __init__(self, filename):
        ADwin.Boot(filename)

    def load_process(self, filename):
        ''' Loads a process onto the ADwin from a binary file. '''
        ADwin.Load_Process(filename)
