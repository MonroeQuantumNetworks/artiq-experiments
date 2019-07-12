"""This idle program reads out 8 counters while blinking "I D L E" in morse code on LED0."""

from artiq.experiment import *
from artiq.coredevice.exceptions import RTIOOverflow
import numpy as np

class idle_counters(EnvExperiment):
    def build(self):

        self.setattr_device("core")
        self.setattr_device("led0")
        self.channel_names = ["ttl0", "ttl1", "ttl2", "ttl3"]
        self.num_channels = len(self.channel_names)
        for ch in self.channel_names:
            self.setattr_device(ch)
        self.channels = [getattr(self, ch) for ch in self.channel_names]

    @kernel
    def run(self):

        # spell "IDLE" in morse code
        morse = [1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]

        self.core.reset()

        # setup inputs
        for channel in self.channels:
            channel.input()

        gate_end_mu = np.full(self.num_channels, 0)
        num_rising_edges = np.full(self.num_channels, 0)

        morse_index = 0
        while True:

            # allow whatever slack is necessary
            self.core.break_realtime()

            # acquire counts
            try:

                # blink the next morse dih-dah on the LED
                if morse[morse_index]:
                    self.led0.on()
                else:
                    self.led0.off()
                # advance to the next dih-dah
                morse_index = (morse_index + 1) % len(morse)

                # acquire counts on all input channels
                gate_t = self.core.seconds_to_mu(1000*ms)
                t = now_mu()  # mark the time before the gate_opens
                for ch in range(self.num_channels):
                    gate_end_mu[ch] = self.channels[ch].gate_rising_mu(gate_t)
                    at_mu(t)  # rewind the time cursor

                # readout all input channels
                for ch in range(self.num_channels):
                    num_rising_edges[ch] = self.channels[ch].count(gate_end_mu[ch])
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
                # update the dataset, which will trigger a plot update
                self.set_dataset("detectors", num_rising_edges, broadcast=True)