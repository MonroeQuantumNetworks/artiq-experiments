"""This idle program reads out 8 counters while blinking "I D L E" in morse code on LED0."""

from artiq.experiment import *
from artiq.coredevice.exceptions import RTIOOverflow
import numpy as np
import base_experiment

class idle_counters(EnvExperiment):

    def build(self):

        #super().build()


        self.setattr_device("core")
        self.setattr_device("scheduler")
        self.setattr_device("led0")

        self.counter_channel_names = ['ttl0', 'ttl1']
        self.num_counter_channels = len(self.counter_channel_names)
        for ch in self.counter_channel_names:
            self.setattr_device(ch)
        self.counter_channels = [getattr(self, ch) for ch in self.counter_channel_names]

    def run(self):

        try:  # catch TerminationRequested

            self.core.break_realtime()

            # spell "IDLE" in morse code
            self.morse = [1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]

            self.gate_end_mu = np.full(self.num_counter_channels, 0)
            self.num_rising_edges = np.full(self.num_counter_channels, 0)

            self.morse_index = 0

            while True:

                self.core.break_realtime()
                self.kernel_run()
                self.core.break_realtime()

                # allow other experiments to preempt
                self.scheduler.pause()

        except TerminationRequested:
            print("Terminated gracefully")

    @kernel
    def kernel_run(self):

        print("idle_counters kernel starting")
        while not self.scheduler.check_pause():
            print("idle_counters kernel loop running...")

            # allow whatever slack is necessary
            self.core.break_realtime()

            # acquire counts
            try:

                # blink the next morse dih-dah on the LED
                if self.morse[self.morse_index]:
                    self.led0.on()
                else:
                    self.led0.off()
                # advance to the next dih-dah
                self.morse_index = (self.morse_index + 1) % len(self.morse)

                # acquire counts on all input channels
                gate_t = self.core.seconds_to_mu(1000*ms)
                t = now_mu()  # mark the time before the gate_opens
                for ch in range(self.num_counter_channels):
                    self.gate_end_mu[ch] = self.counter_channels[ch].gate_rising_mu(gate_t)
                    at_mu(t)  # rewind the time cursor

                # readout all input channels
                for ch in range(self.num_counter_channels):
                    self.num_rising_edges[ch] = self.counter_channels[ch].count(self.gate_end_mu[ch])
            except RTIOOverflow:
                print("RTIO input overflow")

                # clear counters, but set to 1 not 0 so we can tell when the error actually clears
                for ch in range(self.num_counter_channels):
                    self.num_rising_edges[ch] = 1

                not_clear = True
                while not_clear:
                    not_clear = False
                    try:
                        for ch in range(self.num_counter_channels):
                            self.num_rising_edges[ch] = self.counter_channels[ch].count(now_mu())
                            if self.num_rising_edges[ch] != 0:
                                not_clear = True
                    except RTIOOverflow:
                        print("RTIO input overflow")
                        not_clear = True
                    else:
                        print("RTIO input overflow solved")
            else:
                # update the dataset, which will trigger a plot update
                self.set_dataset("detectors", self.num_rising_edges, broadcast=True)