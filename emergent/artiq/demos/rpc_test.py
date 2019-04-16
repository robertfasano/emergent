from artiq.experiment import *
import numpy as np

class Transfer(EnvExperiment):
    def build(self):
        self.setattr_device("core")

    def run(self):
        # bytes = 10**6
        bytes = np.logspace(0, 7, 100)
        print(repr(bytes))
        speed = []
        for b in bytes:
            speed.append(self.transfer_bytes(int(b)))
        # print(self.transfer_integers(int(bytes/4)), "B/s")
        # print(self.transfer_floats(int(bytes/8)), "B/s")
        print(speed)

    def get_bytes(self, n) -> TBytes:
        return b"\x00"*n

    def get_integers(self, n) -> TList(TInt32):
        return [0]*n

    def get_floats(self, n) -> TList(TFloat):
        return [0.0]*n

    @kernel
    def transfer_bytes(self, n):
        t0 = self.core.get_rtio_counter_mu()
        self.get_bytes(n)
        t1 = self.core.get_rtio_counter_mu()
        return n/self.core.mu_to_seconds(t1-t0)

    @kernel
    def transfer_integers(self, n):
        t0 = self.core.get_rtio_counter_mu()
        self.get_integers(n)
        t1 = self.core.get_rtio_counter_mu()
        return n/self.core.mu_to_seconds(t1-t0)

    @kernel
    def transfer_floats(self, n):
        t0 = self.core.get_rtio_counter_mu()
        self.get_floats(n)
        t1 = self.core.get_rtio_counter_mu()
        return n/self.core.mu_to_seconds(t1-t0)
