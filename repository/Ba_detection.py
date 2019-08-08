"""This idle program reads out 8 counters while blinking "I D L E" in morse code on LED0."""

from artiq.language.core import kernel, delay, delay_mu, now_mu, at_mu
from artiq.language.units import s, ms, us, ns, MHz
from artiq.coredevice.exceptions import RTIOOverflow
from artiq.experiment import NumberValue
import numpy as np
import base_experiment


class Ba_detection(base_experiment.base_experiment):

    def build(self):
        super().build()
        self.setattr_argument('detections_per_point', NumberValue(100, ndecimals=0, min=1, step=1))
        self.setattr_argument('max_trials_per_point', NumberValue(10000, ndecimals=0, min=1, step=1))

    @kernel
    def cool(self):
        self.DDS__493__Bob__sigma_1.sw.on()
        delay_mu(10)
        self.DDS__493__Bob__sigma_2.sw.on()
        delay_mu(10)
        self.DDS__493__Bob__pi.sw.on()
        delay_mu(10)
        delay(self.globals__timing__cooling_time)
        delay_mu(10)
        self.DDS__493__Bob__sigma_1.sw.off()
        delay_mu(10)
        self.DDS__493__Bob__sigma_2.sw.off()
        delay_mu(10)
        self.DDS__493__Bob__pi.sw.off()
        delay_mu(10)

    @kernel
    def pump1(self):
        self.DDS__493__Bob__sigma_1.sw.pulse(self.globals__timing__pumping_time)

    @kernel
    def pump2(self):
        self.DDS__493__Bob__sigma_2.sw.pulse(self.globals__timing__pumping_time)

    @kernel
    def get_counts(self):
        return self.Bob_camera_side_APD.count(self.Bob_camera_side_APD.gate_rising(self.globals__timing__detection_time))

    @kernel
    def detect1(self):
        self.DDS__493__Bob__sigma_1.sw.on()
        counts = self.get_counts()
        self.DDS__493__Bob__sigma_1.sw.off()
        return counts

    @kernel
    def detect2(self):
        self.DDS__493__Bob__sigma_2.sw.on()
        counts = self.get_counts()
        self.DDS__493__Bob__sigma_2.sw.off()
        return counts

    @kernel
    def setup(self):
        self.DDS__493__Bob__sigma_1.sw.off()
        delay_mu(10)
        self.DDS__493__Bob__sigma_2.sw.off()
        delay_mu(10)
        self.DDS__650__sigma_1.sw.on()
        delay_mu(10)
        self.DDS__650__sigma_2.sw.on()
        delay_mu(10)
        self.DDS__650__Bob__pi.sw.on()
        delay_mu(10)
        self.DDS__650__fast_AOM.sw.on()
        delay_mu(10)
        self.DDS__493__Bob__pi.sw.off()
        delay_mu(10)

    @kernel
    def run(self):

        self.core.reset()

        self.setup()

        trials = 0
        sum1 = 0
        sum2 = 0

        while (trials <= self.max_trials_per_point) and ((sum1 + sum2) < self.detections_per_point):

            print(trials)
            self.core.break_realtime()

            # allow whatever slack is necessary

            delay(1 * ms)
            self.cool()
            self.pump1()
            sum2 += self.detect1()

            delay(1 * ms)
            self.cool()
            self.pump2()
            sum2 += self.detect2()

            trials += 1

        # export ratio of detections
        ratio = sum1/(sum1 + sum2)
        print('ratio', ratio)
        self.set_dataset('ratio', ratio, broadcast=True, archive=True)

