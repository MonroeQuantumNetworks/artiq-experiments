
import traceback

from artiq.experiment import *
#from artiq.language.core import kernel, delay
#from artiq.language.environment import EnvExperiment
#from artiq.language.units import s, ms, us, ns, MHz
import base_experiment

class Fast_DDS_Pulse_Test(base_experiment.base_experiment):
    def build(self):
        super().build()
        #self.setattr_argument('pulse_length', NumberValue(1e-8, unit="ns", ndecimals=0, min=1*ns, step=1*ns))
        #self.setattr_argument('pulse_number', NumberValue(10000, ndecimals=0, min=100, step=100))
        self.setattr_device("core_dma")

    @kernel
    def record_fast_pulse(self):
        with self.core_dma.record("pulses"):
            self.ttl8.pulse(100*ns) # trigger for oscilloscope
            delay(200*ns)
            self.urukul3_ch1.sw.pulse(10*ns)
            delay(100*ns)

    @kernel
    def set_DDS_freq(self, channel, freq):
        self.core.reset()
        delay_mu(95000)
        channel.set_frequency(freq)
        delay_mu(6000)

    @kernel
    def run(self):
        self.core.reset()
        self.urukul3_ch1.sw.off()
        self.record_fast_pulse()
        pulse_handle = self.core_dma.get_handle("pulses")
        self.core.break_realtime()
        try:
            self.set_DDS_freq(self.urukul3_ch1, 400*MHz)
            while True:
                delay_mu(100000)
                self.core_dma.playback_handle(pulse_handle)
        except TerminationRequested:
            print('Terminated gracefully')

    # @kernel
    # def kernel_run(self):
    #     self.record_fast_pulse()
    #     pulse_handle = self.core_dma.get_handle("pulses")
    #     self.core.break_realtime()
    #     self.core_dma.playback_handle(pulse_handle)