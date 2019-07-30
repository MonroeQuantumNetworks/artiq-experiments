from artiq.experiment import *
from artiq.coredevice.exceptions import RTIOOverflow

class counter_test2(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl0")

    @kernel
    def run(self):
        self.core.reset()
        self.ttl0.input()
        while True:
            self.core.break_realtime()

            # acquire counts
            try:
                gate_end_mu = self.ttl0.gate_rising(1*s)
                num_rising_edges0 = self.ttl0.count(gate_end_mu)
            except RTIOOverflow:
                print("RTIO input overflow")

                # clear counters
                num_rising_edges0 = 1
                while (num_rising_edges0 != 0):
                    try:
                        num_rising_edges0 = self.ttl0.count(now_mu())
                    except RTIOOverflow:
                        print("RTIO input overflow")
                    else:
                        print("cleared")
            else:
                print(num_rising_edges0)

            delay(100*ms)
