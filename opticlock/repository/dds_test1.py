from artiq.experiment import *


class dds_test1(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("led0")
        self.setattr_device("led1")
        self.setattr_device("ttl8")
        self.setattr_device("ttl9")
        self.setattr_device("ttl10")
        self.setattr_device("ttl11")
        self.setattr_device("urukul0_cpld")
        self.setattr_device("urukul0_ch0")
        self.setattr_device("urukul0_ch1")
        self.setattr_device("urukul0_ch2")
        self.setattr_device("urukul0_ch3")
    
    @kernel
    def rf_switch_wave(self, channels):
        while True:
            self.core.break_realtime()
            # do not fill the FIFOs too much to avoid long response times
            t = now_mu() - self.core.seconds_to_mu(0.2)
            while self.core.get_rtio_counter_mu() < t:
                pass
            for channel in channels:
                channel.pulse(100*ms)
                delay(100*ms)
    
    @kernel
    def init_urukul(self, cpld):
        self.core.break_realtime()
        cpld.init()
    
    @kernel
    def setup_urukul(self, channel, frequency):
        self.core.break_realtime()
        channel.init()
        channel.set(frequency*MHz)
        channel.sw.on()
        channel.set_att(14.)
    
    # We assume that RTIO channels for switches are grouped by card.
    @kernel
    def test_urukuls(self):
        self.init_urukul(self.urukul0_cpld)
        #print("urukul0 initialized")
        
        self.setup_urukul(self.urukul0_ch0, 100)  # 1 MHz
        #print("urukul 0 channel 0 setup")

        #self.rf_switch_wave([self.urukul0_ch0.sw])

    @kernel
    def run(self):
        start_time = now_mu() + self.core.seconds_to_mu(500*ms)
        while self.core.get_rtio_counter_mu() < start_time:
            pass
        self.core.break_realtime()

        self.ttl8.pulse(20*ns)

        self.test_urukuls()

        self.core.break_realtime()

        self.ttl9.pulse(20*ns)
        #self.ttl10.pulse(20*ns)
        #self.ttl11.pulse(20*ns)
        
