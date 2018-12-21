from emergent.modules import Watchdog

class LabJackWatchdog(Watchdog):
    def __init__(self, parent, experiment, threshold, name = 'watchdog'):
        super().__init__(parent, experiment, name = name)
        self.threshold = threshold
