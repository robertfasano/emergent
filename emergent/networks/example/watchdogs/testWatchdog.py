from emergent.modules import Watchdog

class TestWatchdog(Watchdog):
    def __init__(self, parent, experiment, threshold = 0.5, name = 'watchdog'):
        super().__init__(parent, experiment, threshold, name = name)

    def react(self):
        self.reoptimize(self.parent.state, 'transmitted_power')
