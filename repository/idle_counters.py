"""This idle program reads out 8 counters while blinking "I D L E" in morse code on LED0."""

from artiq.language.core import kernel, delay, at_mu, now_mu
from artiq.experiment import NumberValue, TerminationRequested
from artiq.language.units import s, ms, us, ns, MHz
from artiq.coredevice.exceptions import RTIOOverflow
import numpy as np
import base_experiment

class idle_counters(base_experiment.base_experiment):

    def build(self):

        super().build()
        self.setattr_argument('detection_time', NumberValue(100*ms, unit='ms', ndecimals=9, min=0, step=1.0))
        print('idle_counters.py build() done')

    def run(self):

        self.gate_t = self.core.seconds_to_mu(self.detection_time)

        try:  # catch TerminationRequested

            # spell "IDLE" in morse code
            self.morse = [1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]

            self.gate_end_mu = np.full(self.globals__TTL_input__num_channels, 0)
            self.num_rising_edges = np.full(self.globals__TTL_input__num_channels, 0)

            self.morse_index = 0

            while True:

                self.setup()

                self.kernel_run()

                # allow other experiments to preempt
                self.core.comm.close()
                print("idle_counters.py: pause")
                self.scheduler.pause()
                print("idle_counters.py: unpause")


        except TerminationRequested:
            print('Terminated gracefully')

    @kernel
    def kernel_run(self):

        self.core.reset()

        while not self.scheduler.check_pause():

            # allow whatever slack is necessary and clear inputs
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
                t = now_mu()  # mark the time before the gate_opens
                for ch in range(self.globals__TTL_input__num_channels):
                    self.num_rising_edges[ch] = 0
                    self.gate_end_mu[ch] = self.TTL_input_channels[ch].gate_rising_mu(self.gate_t)
                    at_mu(t+ch*10)  # rewind the time cursor with an offset of 10 machine units per channel to prevent collisions

                # consume events in a round-robin
                while self.core.get_rtio_counter_mu() < self.gate_end_mu[0]:
                    # readout all input channels
                    for ch in range(self.globals__TTL_input__num_channels):
                        self.num_rising_edges[ch] += self.TTL_input_channels[ch].count(self.core.get_rtio_counter_mu())

            except RTIOOverflow:
                print("RTIO input overflow")
                self.core.reset()
            else:
                # update the dataset, which will trigger a plot update
                self.set_dataset("detectors", self.num_rising_edges, broadcast=True, persist=True)