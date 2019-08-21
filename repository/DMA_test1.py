from artiq.experiment import *
import base_experiment
from artiq.language.environment import HasEnvironment, EnvExperiment

class DMA_test1(base_experiment.base_experiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("core_dma")
        self.setattr_device("ttl8")
        self.setattr_device("ttl9")

    @kernel
    def record(self):
        with self.core_dma.record("pulses"):
            # all RTIO operations now go to the "pulses"
            # DMA buffer, instead of being executed immediately.
            for i in range(100):
                self.ttl8.pulse(200*ns)
                # self.ttl9.pulse(1*us)
                # self.ttl8.pulse(10*ns)
                # self.ttl9.pulse(1*us)
                delay(100*ns)

    @kernel
    def run(self):
        self.core.reset()
        self.record()
        # prefetch the address of the DMA buffer
        # for faster playback trigger
        pulses_handle = self.core_dma.get_handle("pulses")
        self.coreanalyzer_purge()
        self.core.break_realtime()
        try:
            while True:
                delay(10000*ns)
                # execute RTIO operations in the DMA buffer
                # each playback advances the timeline by 50*(100+100) ns
                self.core_dma.playback_handle(pulses_handle)
        finally:
            delay_mu(18000)
            self.coreanalyzer_write()
