from artiq.experiment import *
from artiq.coredevice.exceptions import RTIOOverflow
import numpy as np

class counter_test1(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.iterations = 100
        self.channel_names = ["ttl0", "ttl1", "ttl2", "ttl3"]
        self.num_channels = len(self.channel_names)
        for ch in self.channel_names:
            self.setattr_device(ch)
        self.channels = [getattr(self, ch) for ch in self.channel_names]
        self.set_dataset("detectors", np.full((self.iterations, self.num_channels), np.nan, dtype=int), broadcast=True)
        self.set_dataset("points", 0, broadcast=True)

    @kernel
    def run(self):
        self.core.reset()
        for channel in self.channels:
            channel.input()

        gate_end_mu = np.full(self.num_channels, 0)
        num_rising_edges = np.full(self.num_channels, 0)

        for i in range(self.iterations):

            self.core.break_realtime()

            # acquire counts
            try:
                with parallel:
                    gate_t = 100*ms
                    for ch in range(self.num_channels):
                        gate_end_mu[ch] = self.channels[ch].gate_rising(gate_t)
                for ch in range(self.num_channels):
                    num_rising_edges[ch] = self.channels[ch].count(gate_end_mu[ch])+ch
            except RTIOOverflow:
                print("RTIO input overflow")

                # clear counters, but set to 1 not 0 so we can tell when the error actually clears
                for ch in range(self.num_channels):
                    num_rising_edges[ch] = 1

                not_clear = True
                while not_clear:
                    not_clear = False
                    try:
                        for ch in range(self.num_channels):
                            num_rising_edges[ch] = self.channels[ch].count(now_mu())
                            if num_rising_edges[ch] != 0:
                                not_clear = True
                    except RTIOOverflow:
                        print("RTIO input overflow")
                        not_clear = True
                    else:
                        print("RTIO input overflow solved")
            else:
                for ch in range(self.num_channels):
                    self.mutate_dataset("detectors", ((i, i+1, None), (ch, ch+1, None), ), num_rising_edges[ch])

            delay(100*ms)
            i += 1  # increase iteration number
            self.set_dataset("points", i, broadcast=True)
