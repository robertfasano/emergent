''' The DAQ class allows the definition of data acquisition objects which
    can attach to nodes to allow sequenced read/writes through the usual
    framework.
'''
class DAQ():
    def __init__(self):
        return

    def _bind(self, channel):
        ''' Called by a node to attach an actuation or cost method to a channel
            on the DAQ. This allows simple sequenced reads and prevents
            multiple processes from claiming the same channel accidentally. '''

    def _read(self, channel):
        ''' Returns a reading for the targeted channel. '''
