from emergent.modules import Watchdog

class TestWatchdog(Watchdog):
    def __init__(self, parent, experiment, name = 'watchdog'):
        super().__init__(parent, experiment, name = name)
        self.threshold = 0.5

    def react(self):
        self.reoptimize(self.parent.state, 'transmitted_power')
