from artiq.experiment import *


class led_test1(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("led0")
        self.setattr_device("led1")

    @kernel
    def run(self):
        start_time = now_mu() + self.core.seconds_to_mu(500*ms)
        while self.core.get_rtio_counter_mu() < start_time:
            pass
        self.core.reset()
        while True:
            self.led0.pulse(500*ms)
            self.led1.pulse(500*ms)
