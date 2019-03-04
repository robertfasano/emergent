
class DashAPI():
    def __init__(self, dashboard):
        self.dashboard = dashboard

    def get(self, target):
        if target == 'state':
            return self.dashboard.tree_widget.get_state()

    def set(self, target, value):
        if target == 'state':
            self.dashboard.tree_widget.set_state(value)


class MainAPI():
    def __init__(self, network):
        self.network = network

    def get(self, target):
        if target == 'state':
            return self.network.state()

        if target == 'settings':
            return self.network.settings()

    def set(self, target, value):
        if target == 'state':
            self.network.actuate(value, send_over_p2p = False)

        elif target == 'settings':
            self.network.set_settings(value)
