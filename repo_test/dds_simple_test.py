import time

from artiq.experiment import *
import base_experiment

class dds_simple_test(base_experiment.base_experiment):
    def build(self):
        super().build()

    @kernel
    def kernel_run(self):
        self.core.reset()
        with parallel:
            self.urukul0_ch0.sw.on()
            self.urukul1_ch0.sw.on()
            self.urukul1_ch1.sw.on()
            self.urukul1_ch2.sw.on()
        delay(2*us)
        with parallel:
            self.urukul0_ch0.sw.off()
            self.urukul1_ch0.sw.off()
            self.urukul1_ch1.sw.off()
            self.urukul1_ch2.sw.off()
        delay(2*us)
        with parallel:
            self.urukul0_ch0.sw.on()
            self.urukul1_ch0.sw.on()
            self.urukul1_ch1.sw.on()
            self.urukul1_ch2.sw.on()
        delay(2 * us)
        with parallel:
            self.urukul0_ch0.sw.off()
            self.urukul1_ch0.sw.off()
            self.urukul1_ch1.sw.off()
            self.urukul1_ch2.sw.off()
        delay(2 * us)
        with parallel:
            self.urukul0_ch0.sw.on()
            self.urukul1_ch0.sw.on()
            self.urukul1_ch1.sw.on()
            self.urukul1_ch2.sw.on()
        delay(2 * us)
        with parallel:
            self.urukul0_ch0.sw.off()
            self.urukul1_ch0.sw.off()
            self.urukul1_ch1.sw.off()
            self.urukul1_ch2.sw.off()

    def run(self):
        start_time = time.time()
        self.kernel_run()
        print("End time: {}".format(time.time() - start_time))
