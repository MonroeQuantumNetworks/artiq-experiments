from artiq.experiment import *
from artiq.coredevice.exceptions import RTIOOverflow

class counter_test1(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl0")
        self.setattr_device("ttl1")

    @kernel
    def run(self):
        self.core.reset()
        self.ttl0.input()
        self.ttl1.input()
        while True:
            self.core.break_realtime()

            # acquire counts
            try:
                with parallel:
                    gate_t = 10*us
                    gate_end_mu = self.ttl0.gate_rising(gate_t)
                    gate_end_mu = self.ttl1.gate_rising(gate_t)
                num_rising_edges0 = self.ttl0.count(gate_end_mu)
                num_rising_edges1 = self.ttl1.count(gate_end_mu)
            except RTIOOverflow:
                print("RTIO input overflow")

                # clear counters
                num_rising_edges0 = 1
                num_rising_edges1 = 1
                while (num_rising_edges0 != 0) or (num_rising_edges1 != 0):
                    try:
                        num_rising_edges0 = self.ttl0.count(now_mu())
                        num_rising_edges1 = self.ttl1.count(now_mu())
                    except RTIOOverflow:
                        print("RTIO input overflow")
                    else:
                        print(num_rising_edges0, num_rising_edges1)
            else:
                print(num_rising_edges0, num_rising_edges1)

            delay(100*ms)

