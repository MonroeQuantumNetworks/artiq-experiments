from artiq.experiment import *


class DMA_test1(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("core_dma")
        self.setattr_device("ttl8")

    @kernel
    def record(self):
        with self.core_dma.record("pulses"):
            # all RTIO operations now go to the "pulses"
            # DMA buffer, instead of being executed immediately.
            for i in range(10000):
                delay(20*ns)
                self.ttl8.pulse(8*ns)

    @kernel
    def run(self):
        start_time = self.core.get_rtio_counter_mu() + self.core.seconds_to_mu(1)
        while self.core.get_rtio_counter_mu() < start_time:
            pass
        self.core.reset()
        delay(1*s)
        self.record()
        # prefetch the address of the DMA buffer
        # for faster playback trigger
        pulses_handle = self.core_dma.get_handle("pulses")
        while True:
            self.core.break_realtime()
            # execute RTIO operations in the DMA buffer
            # each playback advances the timeline by 50*(100+100) ns
            self.core_dma.playback_handle(pulses_handle)