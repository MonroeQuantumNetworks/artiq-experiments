from artiq.experiment import *


class ttl_test1(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("led0")
        self.setattr_device("led1")
        self.setattr_device("ttl8")
        self.setattr_device("ttl9")
        self.setattr_device("ttl10")
        self.setattr_device("ttl11")

    @kernel
    def run(self):
        start_time = self.core.get_rtio_counter_mu() + self.core.seconds_to_mu(1)
        while self.core.get_rtio_counter_mu() < start_time:
            pass
        self.core.reset()
        delay(1*s)
        for i in range(10):
            self.core.break_realtime()
            #delay(100*ns)
            #self.core.break_realtime()
            self.ttl8.pulse(10*ms)
            rtio_log("ttl8", "i", i)
            delay(10*ms)
            #self.ttl9.pulse(8*ns)
            #self.ttl8.pulse(8*ns)
            #self.ttl10.pulse(8*ns)
            #self.ttl8.pulse(8*ns)
            #self.ttl11.pulse(8*ns)
