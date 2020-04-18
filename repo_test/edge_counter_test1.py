# This file only works with ARTIQ >= 5.0
# It is a test of the new edge_counter class, which counts without saving timestamps of individual clicks.
# MTL 2010-06-28

from artiq.experiment import *
from artiq.coredevice.edge_counter import CounterOverflow

class edge_counter_test1(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        #self.setattr_device("ttl0")
        self.setattr_device("ttl0_counter")

    @rpc(flags={"async"})
    def print_counts(self, counts):
        print('count = ', counts)

    @kernel
    def run(self):
        self.core.reset()
        #self.ttl0.input()
        while True:
            self.core.break_realtime()
            # acquire counts
            self.ttl0_counter.gate_rising(1 * ms)
            delay(100*ms)
            num_rising_edges = self.ttl0_counter.fetch_count()
            self.print_counts(num_rising_edges)
