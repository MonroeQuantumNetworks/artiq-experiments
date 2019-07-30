"""This idle program reads out 8 counters while blinking "I D L E" in morse code on LED0."""

from artiq.experiment import *  # NumberValue, delay, now_mu, at_mu, kernel
from artiq.coredevice.exceptions import RTIOOverflow
import numpy as np
import base_experiment

class Ba_detection(base_experiment.base_experiment):

    def build(self):

        # setup channels
        super().load_globals_from_dataset()
        super().build_common()

        self.setattr_argument('detections_per_point', NumberValue(100, ndecimals=0, min=1, step=1))
        self.setattr_argument('max_trials_per_point', NumberValue(10000, ndecimals=0, min=1, step=1))
        self.active_detector_channels = [self.detect0, self.detect1]

    @kernel
    def cool(self):
        self.DDS['493_s-'].on()
        self.DDS['493_pi'].on()
        self.DDS['493_s+'].on()
        delay(self.cooling_time)
        self.DDS['493_s-'].off()
        self.DDS['493_pi'].off()
        self.DDS['493_s+'].off()

    @kernel
    def pump0(self):
        self.DDS['493_s-'].on()
        delay(self.pumping_time)
        self.DDS['493_s-'].off()

    @kernel
    def pump1(self):
        self.DDS['493_s+'].on()
        delay(self.pumping_time)
        self.DDS['493_s+'].off()

    @kernel
    def detect0(self):
        self.DDS['493_s-'].on()
        delay(self.detection_time)
        self.DDS['493_s-'].off()

    @kernel
    def detect1(self):
        self.DDS['493_s+'].on()
        delay(self.detection_time)
        self.DDS['493_s+'].off()

    """
    @kernel
    def acquire_counts:
            try:
                # acquire counts on all input channels
                gate_t = self.core.seconds_to_mu(self.detection_time)
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
    """

    def run(self):
        #self.cooling_time = getattr(self, 'global.cooling.cooling_time')
        print(dir(self))

    @kernel
    def kernel_run(self):

        self.core.break_realtime()

        trials = 0
        self.detect0 = 0
        self.detect1 = 0

        # holder for detector counts
        gate_end_mu = np.full(self.num_channels, 0)
        num_rising_edges = np.full(self.num_channels, 0)

        while (trials <= self.max_trials_per_point) and ((detect0 + detect1) < self.detections_per_point):

            # allow whatever slack is necessary
            self.core.break_realtime()

            self.cool()
            self.pump0()
            self.detect0()

            self.cool()
            self.pump1()
            self.detect1()

            trials += 1

        # export ratio of detections
        self.set_dataset('ratio', self.detect0/(self.detect0 + self.detect1))

