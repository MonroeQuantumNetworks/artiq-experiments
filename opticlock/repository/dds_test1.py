from artiq.experiment import *


class dds_test1(EnvExperiment):

    def build(self):

        self.setattr_argument("ch0_freq", NumberValue(1.0, ndecimals=1, min=0.0, max=500.0, step=1.0))
        self.setattr_argument("ch1_freq", NumberValue(1.0, ndecimals=1, min=0.0, max=500.0, step=1.0))
        self.setattr_argument("ch2_freq", NumberValue(1.0, ndecimals=1, min=0.0, max=500.0, step=1.0))
        self.setattr_argument("ch3_freq", NumberValue(1.0, ndecimals=1, min=0.0, max=500.0, step=1.0))
        self.setattr_argument("ch0_amp", NumberValue(10.0, ndecimals=1, min=0.0, max=31.5, step=0.5))
        self.setattr_argument("ch1_amp", NumberValue(10.0, ndecimals=1, min=0.0, max=31.5, step=0.5))
        self.setattr_argument("ch2_amp", NumberValue(10.0, ndecimals=1, min=0.0, max=31.5, step=0.5))
        self.setattr_argument("ch3_amp", NumberValue(10.0, ndecimals=1, min=0.0, max=31.5, step=0.5))

        self.setattr_device("core")
        self.setattr_device("urukul0_cpld")
        self.setattr_device("urukul0_ch0")
        self.setattr_device("urukul0_ch1")
        self.setattr_device("urukul0_ch2")
        self.setattr_device("urukul0_ch3")

    @kernel
    def setup_urukul(self, channel, frequency=100.0, attenuation=31.5):
        """Setup one DDS channel.

        :param channel: The DDS channel, i.e. "self.urukul0_ch0"
        :param frequency: The frequency in MHz.
        :param attenuation: The attenuation in dB, 0 maximum attenuation (31.5 dB), max output power ~10 dBm so 0 att = 10 dBm and -31.5 att = -21.5 dB.  More attenuation = less power.
        """

        self.core.break_realtime()
        channel.init()
        channel.set(frequency*MHz)  # set freq in MHz
        channel.sw.on()
        channel.set_att(attenuation)  # set attenuation in dB 0 to 31.5, base level is +10 dBm.

    @kernel
    def ch_off(self, channel):
        """Setup one DDS channel.

        :param channel: The DDS channel, i.e. "self.urukul0_ch0"
        :param frequency: The frequency in MHz.
        :param attenuation: The attenuation in dB, 0 maximum attenuation (31.5 dB), max output power ~10 dBm so 0 att = 10 dBm and -31.5 att = -21.5 dB.  More attenuation = less power.
        """

        self.core.break_realtime()
        channel.init()
        channel.set(1*Hz)  # set freq in MHz
        channel.sw.off()
        channel.set_att(31.5)

    @kernel
    def run(self):
        self.core.reset()
        self.core.break_realtime()

        self.urukul0_cpld.init()

        #self.ch_off(self.urukul0_ch0)
        self.setup_urukul(self.urukul0_ch0, self.ch0_freq, self.ch0_amp)
        self.setup_urukul(self.urukul0_ch1, self.ch1_freq, self.ch1_amp)
        self.setup_urukul(self.urukul0_ch2, self.ch2_freq, self.ch2_amp)
        self.setup_urukul(self.urukul0_ch3, self.ch3_freq, self.ch3_amp)

        self.core.break_realtime()
