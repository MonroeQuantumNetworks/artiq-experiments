from artiq.experiment import *
from artiq.coredevice.exceptions import RTIOOverflow

class counter_test1(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl0")

    @kernel
    def run(self):
        self.core.reset()
        self.ttl0.input()
        while True:
            print('acquiring:')
            self.core.break_realtime()

            # acquire counts
            try:
                gate_end_mu = self.ttl0.gate_rising(5 * us)
                for i in range(10):
                    print(self.ttl0.timestamp_mu(gate_end_mu))
            except RTIOOverflow:
                    print('RTIO input overflow')
            print()

            delay(100*ms)

